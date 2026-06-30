# Real Estate Development App for ERPNext

A Frappe/ERPNext app for managing real estate development projects — unit sales, customer bookings, payment plans, bulk payment import, broker commissions, partner profit sharing, and project cost tracking.

## Features

- **Unit & Booking Management** — Create units under projects, manage bookings with full payment plan milestones
- **Payment Plan Templates** — Define installment structures (Down Payment, Monthly Installments, On Possession)
- **Bulk Payment Import** — Import customer payments from CSV with automatic Sales Invoice creation and installment allocation
- **Payment Priority Sorting** — Payments automatically allocated to Down Payment → Monthly Installments → On Possession
- **Reports** — Unit Payment Status, Unit Sales Status, Customer Installment Aging, Project P&L, Project Cost vs Budget, Broker Commission Payable, Partner Capital Statement
- **Dashboard** — Number cards (Total Units, Available Units, Active Bookings, Total Booked Value) + charts (Booking Trends, Units by Status, Project Revenue)
- **Broker Management** — Track broker commissions per booking, generate commission payable reports
- **Partner Capital Accounts** — Manage investment partners, capital contributions, and profit distribution
- **Project Cost Budgeting** — Budget tracking with cost categories, progress claims, and variance reporting

## Requirements

| Dependency | Version |
|------------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| MariaDB | 10.6+ |
| Redis | 6+ |
| Frappe Bench | v15+ |
| ERPNext | v15+ |

---

## Step-by-Step Installation Guide

### Step 1: Install Frappe Bench

Bench is the command-line tool for managing Frappe/ERPNext sites.

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-dev python3-pip python3-venv \
  mariadb-server mariadb-client redis-server nodejs npm \
  libffi-dev libssl-dev wkhtmltopdf

# Install bench
sudo pip3 install frappe-bench

# Initialize bench
bench init frappe-bench --version version-15
cd frappe-bench
```

**macOS:**

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 git mariadb redis node wkhtmltopdf

# Start services
brew services start mariadb
brew services start redis

# Install bench
pip3 install frappe-bench

# Initialize bench
bench init frappe-bench --version version-15
cd frappe-bench
```

### Step 2: Configure MariaDB

```bash
# Secure the installation
sudo mysql_secure_installation

# Create MariaDB configuration
sudo bench setup mariadb
```

### Step 3: Get the ERP_Real_Estate App

```bash
# From your bench directory
bench get-app --branch main https://github.com/Mawj-media/ERP_REAL_ESTATE
```

### Step 4: Get ERPNext (Required Dependency)

```bash
bench get-app --branch version-15 erpnext
```

### Step 5: Create a Site

```bash
bench new-site site1.local --admin-password admin
```

Replace `site1.local` with your desired site name. The `--admin-password` sets the Administrator password.

### Step 6: Install Apps on the Site

```bash
# Install ERPNext first (required dependency)
bench --site site1.local install-app erpnext

# Install the Real Estate app
bench --site site1.local install-app real_estate
```

### Step 7: Build Assets and Migrate

```bash
bench build
bench --site site1.local migrate
```

### Step 8: Start the Development Server

```bash
bench start
```

Access the site at `http://site1.local:8000` in your browser. Log in with:
- **Username:** Administrator
- **Password:** (the password you set with `--admin-password`)

---

## Configuration Guide

### 1. Create a Sale Item

Go to: **Item** → **New**

- Item Code: `UNIT-SALE`
- Item Name: `Unit Sale`
- Item Type: `Service`
- Enable: **Is Sales Item**
- Under **Accounts**: Set **Default Income Account** to `Unit Sales Revenue - {Company Abbr}`

### 2. Configure Real Estate Settings

Go to: **Real Estate Settings** (search in the Awesome Bar)

- **Default Sale Item:** Select the item you created above
- **Default Payment Terms Template:** (optional) Select or create a Payment Terms Template

### 3. Create a Real Estate Project

Go to: **Real Estate Project** → **New**

- **Project Name:** e.g., "Gulshan Heights"
- **Company:** Your company
- **Project Status:** Planning / Construction / Completed / Closed
- **Project Location:** Physical address of the project
- **Total Units:** Number of units in the project

### 4. Set Up Payment Plan Templates

Go to: **Payment Plan Template** → **New**

Define the installment structure for your bookings. Example:

| Milestone Label | Percentage |
|----------------|------------|
| Down Payment | 25% |
| Monthly Installments (24 x 2.5%) | 60% |
| On Possession | 15% |

Create corresponding **Payment Plan Milestone** records for each line item above.

### 5. Create Units

Go to: **Unit** → **New**

- **Unit ID:** e.g., `G-0001`, `0101`, `0305` (any identifier)
- **Project:** Select your Real Estate Project
- **Unit Type:** (optional) Select or create a Unit Type
- **Size:** Area of the unit
- **Price:** Sale price of the unit

### 6. Create a Booking

Go to: **Booking** → **New**

- **Customer:** Select or create a Customer
- **Unit:** Select the unit being sold
- **Project:** Auto-populated from the unit
- **Payment Plan Template:** Select the template
- **Booking Date:** Date of booking

The installments will auto-populate from the payment plan template. Submit the Booking to activate it.

---

## Usage

### Bulk Import Payments

This feature allows you to import multiple customer payments from a CSV file.

1. Go to the **Real Estate** workspace → **Tools** section → **Bulk Import Payments**
2. Click **Download Template** to get the CSV format
3. Fill in the CSV with your payment data:

| customer | booking | amount | payment_date | mode_of_payment | ref_no | ref_date |
|----------|---------|--------|--------------|-----------------|--------|----------|
| John Doe | G-0001 | 500000 | 2026-06-27 | Cash | CASH-001 | 2026-06-27 |

4. Click the upload area and select your CSV file
5. Preview the data with validation feedback
6. Click **Import** to process

**How it works:**
- The app finds the correct Booking by matching the unit identifier in the "booking" column
- If a Sales Invoice doesn't exist for the installment, it is auto-created
- Payments are allocated by priority: Down Payment → Monthly Installments → On Possession
- After allocation, installment fields (paid_amount, outstanding, payment_entry, status) are updated
- A Payment Entry is created and submitted in ERPNext

### Reports

Available under the **Reports** section in the Real Estate workspace:

| Report | Description |
|--------|-------------|
| **Unit Payment Status** | Per-customer view of unit price, total paid, balance, and current payment phase |
| **Unit Sales Status** | Overview of all units with sale status |
| **Customer Installment Aging** | Aging analysis of overdue installments |
| **Project P&L** | Profit and loss by project |
| **Project Cost vs Budget** | Budget vs actual cost comparison |
| **Broker Commission Payable** | Outstanding broker commissions |
| **Partner Capital Statement** | Partner capital account summary |

---

## Project Structure

```
real_estate/
├── hooks.py                        # App hooks, doc events, custom fields
├── modules.txt                     # Module list
├── real_estate/
│   ├── config/                     # Workspace, dashboard config
│   ├── doc_events/                 # ERPNext integration hooks
│   │   ├── payment_entry.py        # Auto-update installments on PE submit/cancel
│   │   └── sales_invoice.py        # Reset installments on SI cancel
│   ├── doctype/                    # Custom DocTypes
│   │   ├── booking/                # Unit booking with installment child table
│   │   ├── unit/                   # Unit master
│   │   ├── real_estate_project/    # Project management
│   │   ├── real_estate_settings/   # Global app settings
│   │   ├── broker/                 # Broker profiles
│   │   ├── partner/                # Investment partners
│   │   ├── payment_plan_template/  # Installment structure definitions
│   │   └── ... (other doctypes)
│   ├── page/
│   │   └── bulk_import_payments/   # CSV payment import page
│   ├── report/                     # Script reports
│   │   ├── unit_payment_status/
│   │   ├── unit_sales_status/
│   │   ├── customer_installment_aging/
│   │   ├── project_pnl/
│   │   └── ...
│   ├── setup/
│   │   └── install.py              # Post-install: creates roles, accounts
│   └── utils/
│       └── bulk_import_payments.py # Core import logic
```

---

## Development

### Running Tests

```bash
bench --site site1.local run-tests --app real_estate
```

### Adding Custom Fields

Custom fields on ERPNext doctypes (Sales Invoice, Purchase Invoice, Payment Entry, Supplier) are defined in `hooks.py` under the `custom_fields` key. Run the following after modifying them:

```bash
bench --site site1.local migrate
```

### Doc Events

The app hooks into these ERPNext events:

| Event | Action |
|-------|--------|
| Payment Entry on_submit | Updates linked Booking Installment paid_amount/outstanding |
| Payment Entry on_cancel | Resets linked Booking Installment to unpaid |
| Sales Invoice on_cancel | Clears installment references and resets to pending |

---

## License

MIT
