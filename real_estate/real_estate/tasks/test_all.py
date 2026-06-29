import frappe, traceback
from frappe.utils import today, flt

def run():
    passed, failed = 0, 0
    def ok(name):
        nonlocal passed; passed += 1
        print(f"  \u2713 {name}")
    def fail(name, err):
        nonlocal failed; failed += 1
        print(f"  \u2717 {name}: {err}")
    def test(name, fn):
        try:
            fn()
            ok(name)
        except Exception as e:
            fail(name, e)

    print("=" * 60)
    print("MOCK DATA & FUNCTIONAL TESTS")
    print("=" * 60)
    unit_name, customer, company, project = "G-0003", "NAVEED SHUJAT", "Choice Builders and Developers", "RE-00001"
    broker_name = "Test Broker"

    broker_doc = None
    # [1] CREATE BROKER
    print("\n[1] BROKER")
    def create_broker():
        nonlocal broker_doc
        frappe.db.sql("DELETE FROM `tabBroker` WHERE broker_name='Test Broker'")
        broker_doc = frappe.get_doc({"doctype":"Broker","broker_name":"Test Broker","commission_rate":1.0,"naming_series":"BKR-"})
        broker_doc.insert()
        assert broker_doc.name, "Broker has no name"
        assert frappe.db.exists("Broker", broker_doc.name), "Broker not found after insert"
        print(f"  Broker {broker_doc.name} created")
    test("Create Broker", create_broker)

    # [2] CREATE BOOKING
    print("\n[2] BOOKING")
    bk = None
    def create_booking():
        nonlocal bk
        u = frappe.get_doc("Unit", unit_name)
        bk = frappe.get_doc({"doctype":"Booking","naming_series":"BK-",
            "customer":customer,"unit":unit_name,
            "sale_value":int(u.current_price),"payment_plan_template":"Standard 24 Month",
            "real_estate_project":project,"booking_date":today(),            "broker":broker_doc.name,
            "broker_commission_rate":1.0})
        bk.insert()
        bk.submit()
        assert bk.name and bk.docstatus == 1, f"Booking not submitted: name={bk.name}, docstatus={bk.docstatus}"
        print(f"  Booking {bk.name} created")
    test("Booking submitted", create_booking)

    inst = None
    def verify_installments():
        nonlocal inst
        bk.reload()
        inst = bk.installments
        assert len(inst) == 3
        assert len([i for i in inst if i.sales_invoice]) == 3
        for pct, i in zip([30,10,60], inst):
            expected = bk.sale_value * pct / 100
            assert abs(i.amount - expected) < 1
            si = frappe.get_doc("Sales Invoice", i.sales_invoice)
            assert si.custom_booking == bk.name
            assert si.docstatus == 1
    test("3 SIs with correct amounts & refs", verify_installments)

    def broker_commission():
        bc = frappe.db.exists("Broker Commission", {"booking": bk.name, "docstatus": 1})
        assert bc
        bc_doc = frappe.get_doc("Broker Commission", bc)
        assert abs(bc_doc.commission_amount - bk.sale_value * 0.01) < 1
    test("Broker Commission at 1%", broker_commission)

    def project_value():
        rp = frappe.get_doc("Real Estate Project", project)
        assert rp.total_sales_value > 0
    test("Project total_sales_value > 0", project_value)

    # [3] PAYMENT ENTRY
    print("\n[3] PAYMENT ENTRY")
    si_name, pay_amount, pe = None, None, None
    def create_pe():
        nonlocal si_name, pay_amount, pe
        si_name = inst[0].sales_invoice
        pay_amount = int(inst[0].amount * 0.5)
        paid_to, paid_from = "Cash - CBD", frappe.db.get_value("Company", company, "default_receivable_account")
        pe = frappe.get_doc({"doctype":"Payment Entry","payment_type":"Receive","party_type":"Customer",
            "party":customer,"company":company,"paid_amount":pay_amount,"received_amount":pay_amount,
            "paid_to":paid_to,"paid_from":paid_from,"mode_of_payment":"Cash",
            "custom_real_estate_project":project,"custom_booking":bk.name,"posting_date":today(),
            "references":[{"reference_doctype":"Sales Invoice","reference_name":si_name,"allocated_amount":pay_amount}]})
        pe.insert()
        pe.submit()
        assert pe.docstatus == 1
    test("Payment Entry created & submitted", create_pe)

    def verify_pe_doc_event():
        bk.reload()
        ui = [i for i in bk.installments if i.sales_invoice == si_name][0]
        assert ui.paid_amount > 0, f"paid_amount=0 (doc_event didn't fire)"
        assert ui.payment_entry == pe.name
    test("PE doc_event updated Booking Installment", verify_pe_doc_event)

    # [4] SUPPLIER + PI + PC
    print("\n[4] PURCHASE INVOICE + PROGRESS CLAIM")
    def create_supplier():
        supplier_name = "Test Contractor"
        frappe.db.sql("DELETE FROM `tabSupplier` WHERE name=%s", supplier_name)
        frappe.get_doc({"doctype":"Supplier","supplier_name":supplier_name,
            "supplier_group":"Services","supplier_type":"Company"}).insert()
        assert frappe.db.exists("Supplier", supplier_name)
    test("Supplier created", create_supplier)

    pi_name = None
    def create_pi():
        nonlocal pi_name
        pi = frappe.get_doc({"doctype":"Purchase Invoice","supplier":"Test Contractor","company":company,
            "posting_date":today(),"custom_real_estate_project":project,
            "custom_cost_category":"Blocks - Labour",
            "items":[{"item_name":"Labour Work","description":"Block work","qty":1,"rate":500000,
                "expense_account":"Loss on Buyback - CBD","cost_center":"Main - CBD"}]})
        pi.insert()
        pi.submit()
        pi_name = pi.name
        assert pi.docstatus == 1
    test("Purchase Invoice created & submitted", create_pi)

    pc_name = None
    def create_pc():
        nonlocal pc_name
        pc = frappe.get_doc({"doctype":"Progress Claim","naming_series":"PC-",
            "contractor":"Test Contractor","real_estate_project":project,"cost_category":"Blocks - Labour",
            "claim_date":today(),"description_of_work":"Test","contract_value":500000,"previous_claimed":0,
            "current_claim_percentage":100,"current_claim_amount":500000,"retention_percentage":10,
            "amount_certified":450000,"net_payable":450000,"certifying_authority":"Engineer",
            "certification_date":today(),"purchase_invoice":pi_name}).insert().submit()
        pc_name = pc.name
        assert pc.docstatus == 1
    test("Progress Claim created & submitted", create_pc)

    # [5] PARTNER CAPITAL ACCOUNT
    print("\n[5] PARTNER CAPITAL ACCOUNT")
    def create_pca():
        partner = frappe.db.sql_list("SELECT name FROM `tabPartner` LIMIT 1")[0]
        pca = frappe.get_doc({"doctype":"Partner Capital Account","naming_series":"PCA-",
            "partner":partner,"real_estate_project":project,"transaction_date":today(),
            "transaction_type":"Capital Contribution","amount":5000000,"mode_of_payment":"Cash","remarks":"Test"}).insert().submit()
        assert pca.docstatus == 1
        pca.cancel()
        frappe.delete_doc("Partner Capital Account", pca.name)
    test("Partner Capital Account", create_pca)

    # [6] UNIT HANDOVER
    print("\n[6] UNIT HANDOVER")
    def create_uh():
        bu = frappe.db.sql("SELECT name FROM `tabBooking` WHERE docstatus=1 AND status='Confirmed' LIMIT 1")
        if bu:
            bh = frappe.get_doc("Booking", bu[0][0])
            uh = frappe.get_doc({"doctype":"Unit Handover","naming_series":"UH-",
                "booking":bh.name,"customer":bh.customer,"unit":bh.unit,
                "real_estate_project":bh.real_estate_project,"handover_date":today(),
                "status":"Pending","total_consideration":bh.sale_value,
                "total_amount_paid":0,"balance_due":bh.sale_value,"maintenance_deposit":50000,
                "legal_charges":25000,"grand_total_due":bh.sale_value+75000}).insert().submit()
            assert uh.docstatus == 1
            uh.cancel()
            frappe.delete_doc("Unit Handover", uh.name)
    test("Unit Handover created, submitted & cleaned", create_uh)

    # [7] CANCEL BOOKING
    print("\n[7] CANCEL BOOKING")
    def cancel_booking():
        bk.reload()
        bk.cancel()
        bk.reload()
        assert bk.status == "Cancelled"
    test("Booking cancelled", cancel_booking)

    def sis_cancelled():
        for i in bk.installments:
            if i.sales_invoice:
                si = frappe.get_doc("Sales Invoice", i.sales_invoice)
                assert si.docstatus == 2, f"SI {si.name} not cancelled"
    test("All SIs cancelled", sis_cancelled)

    def pe_cancelled():
        pe.reload()
        assert pe.docstatus == 2
    test("PE cancelled", pe_cancelled)

    def unit_available():
        assert frappe.get_doc("Unit", unit_name).status == "Available"
    test("Unit back to Available", unit_available)

    def bc_cancelled():
        bc = frappe.db.exists("Broker Commission", {"booking": bk.name})
        if bc:
            assert frappe.get_doc("Broker Commission", bc).docstatus == 2
    test("Broker Commission cancelled", bc_cancelled)

    # [8] DELETE BOOKING
    print("\n[8] DELETE BOOKING")
    def delete_booking():
        frappe.delete_doc("Booking", bk.name)
        assert not frappe.db.exists("Booking", bk.name)
    test("Booking deleted", delete_booking)

    def no_si_refs():
        assert frappe.db.count("Sales Invoice", {"custom_booking": bk.name}) == 0
    test("SI custom_booking references cleared", no_si_refs)

    # SUMMARY
    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")
    if failed:
        print(f"\n{passed}/{passed+failed} tests passed, {failed} failed!")
    else:
        print(f"\nAll {passed} tests passed!")
    return passed, failed

if __name__ == "__main__":
    run()
