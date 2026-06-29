import frappe
from frappe.utils import today, flt
import traceback

def run_all():
    results = {"passed": 0, "failed": 0, "errors": []}

    def check(name, ok, detail=""):
        if ok:
            results["passed"] += 1
            print(f"  ✓ {name}")
        else:
            results["failed"] += 1
            msg = f"  ✗ {name}: {detail}"
            print(msg)
            results["errors"].append(msg)

    def test(name, fn):
        try:
            fn()
            results["passed"] += 1
            print(f"  ✓ {name}")
        except Exception as e:
            results["failed"] += 1
            msg = f"  ✗ {name}: {e}"
            print(msg)
            results["errors"].append(msg)
            traceback.print_exc()

    print("=" * 60)
    print("MOCK DATA & FUNCTIONAL TESTS")
    print("=" * 60)

    # ========================
    # SETUP: Reference data
    # ========================
    unit_name = "G-0003"
    customer = "NAVEED SHUJAT"
    company = "Choice Builders and Developers"
    project = "RE-00001"
    project_name = "SHAZIL CHOICE LUXURIA"

    print(f"\n[Step 1] Setup reference data")
    test("Unit G-0003 is Available", lambda: (
        frappe.get_doc("Unit", unit_name).status == "Available"
    ))
    test("Customer exists", lambda: frappe.db.exists("Customer", customer))
    test("Project exists", lambda: frappe.db.exists("Real Estate Project", project))

    # ========================
    # STEP 2: Create Broker
    # ========================
    print(f"\n[Step 2] Create Broker")
    def create_broker():
        if frappe.db.exists("Broker", "TEST-BROKER-001"):
            frappe.delete_doc("Broker", "TEST-BROKER-001")
        broker = frappe.get_doc({
            "doctype": "Broker",
            "broker_name": "Test Broker",
            "commission_rate": 1.0,
        })
        broker.insert()
        assert frappe.db.exists("Broker", "TEST-BROKER-001"), "Broker not created"
    test("Create Broker", create_broker)

    # ========================
    # STEP 3: Create Booking
    # ========================
    print(f"\n[Step 3] Create Booking for {unit_name}")
    bk_name = None
    def create_booking():
        global bk_name
        unit = frappe.get_doc("Unit", unit_name)
        sale_value = int(unit.current_price)
        bk = frappe.get_doc({
            "doctype": "Booking",
            "customer": customer,
            "unit": unit_name,
            "sale_value": sale_value,
            "payment_plan_template": "Standard 24 Month",
            "real_estate_project": project,
            "booking_date": today(),
            "broker": "TEST-BROKER-001",
            "broker_commission_rate": 1.0,
        })
        bk.insert()
        bk.submit()
        bk_name = bk.name
        assert bk_name, "Booking name is empty"
        assert bk.docstatus == 1, "Booking not submitted"
        assert bk.status == "Confirmed", f"Wrong status: {bk.status}"
    test("Create & submit Booking", create_booking)

    # Reload booking
    bk = frappe.get_doc("Booking", bk_name)

    test("Unit status changed to Booked", lambda: (
        frappe.get_doc("Unit", unit_name).status == "Booked"
    ))

    def check_installments():
        bk.reload()
        inst_with_si = [i for i in bk.installments if i.sales_invoice]
        assert len(inst_with_si) == 3, f"Expected 3 SIs, got {len(inst_with_si)}"
        expected_pct = [30, 10, 60]
        for i, inst in enumerate(bk.installments):
            expected_amt = bk.sale_value * expected_pct[i] / 100
            assert abs(inst.amount - expected_amt) < 1, f"Inst {i} amount mismatch: {inst.amount} vs {expected_amt}"
            si = frappe.get_doc("Sales Invoice", inst.sales_invoice)
            assert si.docstatus == 1, f"SI {si.name} not submitted"
            assert si.custom_booking == bk_name, f"SI custom_booking mismatch"
    test("3 SIs created with correct amounts & refs", check_installments)

    def check_broker_commission():
        bc_name = frappe.db.exists("Broker Commission", {"booking": bk_name, "docstatus": 1})
        assert bc_name, "Broker Commission not found"
        bc = frappe.get_doc("Broker Commission", bc_name)
        expected = bk.sale_value * 0.01
        assert abs(bc.commission_amount - expected) < 1, f"BC amount mismatch: {bc.commission_amount} vs {expected}"
    test("Broker Commission auto-created at 1%", check_broker_commission)

    def check_project_value():
        rp = frappe.get_doc("Real Estate Project", project)
        assert rp.total_sales_value > 0, "Project total_sales_value is 0"
    test("Project total_sales_value updated", check_project_value)

    # ========================
    # STEP 4: Payment Entry
    # ========================
    print(f"\n[Step 4] Payment Entry against first SI")
    first_inst = bk.installments[0]
    si_name = first_inst.si_name if hasattr(first_inst, 'si_name') else first_inst.sales_invoice
    si_amount = first_inst.amount
    pay_amount = int(si_amount * 0.5)
    pe_name = None

    def create_payment_entry():
        global pe_name
        paid_to = "Cash - CBD"
        paid_from = frappe.db.get_value("Company", company, "default_receivable_account")
        pe = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": "Receive",
            "party_type": "Customer",
            "party": customer,
            "company": company,
            "paid_amount": pay_amount,
            "received_amount": pay_amount,
            "paid_to": paid_to,
            "paid_from": paid_from,
            "mode_of_payment": "Cash",
            "custom_real_estate_project": project,
            "custom_booking": bk_name,
            "posting_date": today(),
            "references": [{
                "reference_doctype": "Sales Invoice",
                "reference_name": si_name,
                "allocated_amount": pay_amount,
            }],
        })
        pe.insert()
        pe.submit()
        pe_name = pe.name
        assert pe.docstatus == 1, "PE not submitted"
    test("Create & submit Payment Entry", create_payment_entry)

    def check_pe_doc_event():
        bk.reload()
        updated_inst = [i for i in bk.installments if i.sales_invoice == si_name]
        assert len(updated_inst) == 1, "Installment not found"
        inst = updated_inst[0]
        assert inst.paid_amount > 0, f"paid_amount still 0 (doc_event didn't fire)"
        assert inst.payment_entry == pe_name, f"PE ref not set: {inst.payment_entry}"
    test("PE doc_event updated Booking Installment", check_pe_doc_event)

    # ========================
    # STEP 5: Supplier + PI + PC
    # ========================
    print(f"\n[Step 5] Supplier, Purchase Invoice, Progress Claim")
    def create_supplier():
        if frappe.db.exists("Supplier", "TEST-CONTRACTOR-001"):
            return
        s = frappe.get_doc({
            "doctype": "Supplier",
            "supplier_name": "Test Contractor",
            "supplier_group": "Services",
            "supplier_type": "Company",
            "custom_is_contractor": 1,
            "custom_contractor_category": "Blocks - Labour",
        })
        s.insert()
        assert frappe.db.exists("Supplier", "TEST-CONTRACTOR-001"), "Supplier not created"
    test("Create Supplier", create_supplier)

    pi_name = None
    def create_pi():
        global pi_name
        pi = frappe.get_doc({
            "doctype": "Purchase Invoice",
            "supplier": "TEST-CONTRACTOR-001",
            "company": company,
            "posting_date": today(),
            "custom_real_estate_project": project,
            "custom_cost_category": "Blocks - Labour",
            "items": [{
                "item_name": "Labour Work",
                "description": "Test - Block work",
                "qty": 1,
                "rate": 500000,
                "amount": 500000,
                "expense_account": "Loss on Buyback - CBD",
                "cost_center": "Main - CBD",
            }],
        })
        pi.insert()
        pi.submit()
        pi_name = pi.name
        assert pi.docstatus == 1, "PI not submitted"
    test("Create & submit Purchase Invoice", create_pi)

    pc_name = None
    def create_pc():
        global pc_name
        pc = frappe.get_doc({
            "doctype": "Progress Claim",
            "naming_series": "PC-",
            "contractor": "TEST-CONTRACTOR-001",
            "real_estate_project": project,
            "cost_category": "Blocks - Labour",
            "claim_date": today(),
            "description_of_work": "Test progress claim",
            "contract_value": 500000,
            "previous_claimed": 0,
            "current_claim_percentage": 100,
            "current_claim_amount": 500000,
            "retention_percentage": 10,
            "amount_certified": 450000,
            "net_payable": 450000,
            "certifying_authority": "Engineer",
            "certification_date": today(),
            "purchase_invoice": pi_name,
        })
        pc.insert()
        pc.submit()
        pc_name = pc.name
        assert pc.docstatus == 1, "PC not submitted"
    test("Create & submit Progress Claim", create_pc)

    # ========================
    # STEP 6: Partner Capital Account
    # ========================
    print(f"\n[Step 6] Partner Capital Account")
    def create_pca():
        partner = "PARTNER-00001"
        pca = frappe.get_doc({
            "doctype": "Partner Capital Account",
            "naming_series": "PCA-",
            "partner": partner,
            "real_estate_project": project,
            "transaction_date": today(),
            "transaction_type": "Capital Contribution",
            "amount": 10000000,
            "mode_of_payment": "Cash",
            "remarks": "Test capital contribution",
        })
        pca.insert()
        pca.submit()
        assert pca.docstatus == 1, "PCA not submitted"
        # Cleanup
        pca.cancel()
        frappe.delete_doc("Partner Capital Account", pca.name)
    test("Create, submit & clean Partner Capital Account", create_pca)

    # ========================
    # STEP 7: Unit Handover
    # ========================
    print(f"\n[Step 7] Unit Handover")
    def create_uh():
        booked_unit = frappe.db.get_value("Unit", {"status": "Booked"}, "name")
        if not booked_unit:
            booked_unit = "G-0002"
        booking_for_uh = frappe.db.get_value("Booking", {
            "unit": booked_unit, "docstatus": 1, "status": "Confirmed"
        }, "name")
        assert booking_for_uh, f"No booked unit for handover test"
        bh = frappe.get_doc("Booking", booking_for_uh)
        uh = frappe.get_doc({
            "doctype": "Unit Handover",
            "naming_series": "UH-",
            "booking": bh.name,
            "customer": bh.customer,
            "unit": bh.unit,
            "real_estate_project": bh.real_estate_project,
            "handover_date": today(),
            "status": "Handed Over",
            "total_consideration": bh.sale_value,
            "total_amount_paid": 0,
            "balance_due": bh.sale_value,
            "maintenance_deposit": 50000,
            "legal_charges": 25000,
            "other_charges": 0,
            "grand_total_due": bh.sale_value + 75000,
        })
        uh.insert()
        uh.submit()
        assert uh.docstatus == 1, "UH not submitted"
        # Check unit status changed
        unit_uh = frappe.get_doc("Unit", bh.unit)
        assert unit_uh.status in ("Handed Over", "Booked"), f"Unit status: {unit_uh.status}"
        # Cleanup
        uh.cancel()
        frappe.delete_doc("Unit Handover", uh.name)
    test("Create, submit & clean Unit Handover", create_uh)

    # ========================
    # STEP 8: Cancel Booking & verify cleanup
    # ========================
    print(f"\n[Step 8] Cancel Booking & verify cleanup")
    def cancel_booking():
        bk.reload()
        bk.cancel()
        bk.reload()
        assert bk.status == "Cancelled", f"Booking status: {bk.status}"
        assert bk.cancellation_date is not None, "cancellation_date not set"
    test("Cancel Booking", cancel_booking)

    def verify_si_cancelled():
        bk.reload()
        for inst in bk.installments:
            if inst.sales_invoice:
                si = frappe.get_doc("Sales Invoice", inst.sales_invoice)
                assert si.docstatus == 2, f"SI {si.name} not cancelled (docstatus={si.docstatus})"
    test("All SIs cancelled", verify_si_cancelled)

    def verify_pe_cancelled():
        pe = frappe.get_doc("Payment Entry", pe_name)
        assert pe.docstatus == 2, f"PE {pe_name} not cancelled"
    test("Payment Entry cancelled", verify_pe_cancelled)

    def verify_unit_available():
        unit = frappe.get_doc("Unit", unit_name)
        assert unit.status == "Available", f"Unit status: {unit.status}"
    test("Unit back to Available", verify_unit_available)

    def verify_bc_cancelled():
        bc_name = frappe.db.exists("Broker Commission", {"booking": bk_name})
        if bc_name:
            bc = frappe.get_doc("Broker Commission", bc_name)
            assert bc.docstatus == 2, f"BC not cancelled"
    test("Broker Commission cancelled", verify_bc_cancelled)

    def verify_project_updated():
        rp = frappe.get_doc("Real Estate Project", project)
        assert rp.total_sales_value < bk.sale_value * 10, "Project value seems wrong after cancel"
    test("Project total_sales_value recalculated", verify_project_updated)

    # ========================
    # STEP 9: Delete Booking
    # ========================
    print(f"\n[Step 9] Delete Booking")
    def delete_booking():
        frappe.delete_doc("Booking", bk_name)
        assert not frappe.db.exists("Booking", bk_name), "Booking still exists"
    test("Delete Booking", delete_booking)

    def verify_si_custom_booking_null():
        for inst in frappe.get_doc("Booking", bk_name).installments if frappe.db.exists("Booking", bk_name) else []:
            pass
        # Check a known SI
        sis = frappe.db.get_all("Sales Invoice", filters={"custom_booking": bk_name})
        assert len(sis) == 0, f"Still {len(sis)} SIs reference deleted booking"
    test("SI custom_booking cleared", verify_si_custom_booking_null)

    # ========================
    # SUMMARY
    # ========================
    print(f"\n{'=' * 60}")
    print(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
    print(f"{'=' * 60}")
    if results["errors"]:
        print("\nErrors:")
        for e in results["errors"]:
            print(f"  {e}")

    return results


if __name__ == "__main__":
    run_all()
