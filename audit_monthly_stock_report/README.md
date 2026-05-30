# Audit Monthly Stock Report — Odoo 18 Custom Module

## Overview
Generates a professional multi-sheet Excel report of **current stock quantities**,
filterable by warehouse, location, and product category, directly from a wizard in
the Odoo Inventory menu.

---

## Features
| Feature | Details |
|---|---|
| **Wizard UI** | Filter by Warehouse(s), Location(s), Product Category(ies), zero-stock toggle |
| **Summary sheet** | KPI cards (total products, locations, qty), Top-10 products table |
| **Stock by Location sheet** | Grouped by location with sub-totals and grand total |
| **Professional styling** | Branded headers, alternating row colours, frozen header row |
| **One-click download** | Binary field in wizard → browser download |

---

## Installation

### 1. Prerequisites
```bash
# openpyxl must be available in the Odoo Python environment
pip install openpyxl
```

### 2. Copy the module
```bash
cp -r audit_monthly_stock_report /path/to/your/odoo/addons/
```

### 3. Update the apps list & install
1. Activate **Developer Mode** in Odoo Settings.
2. Go to **Apps → Update Apps List**.
3. Search for **"Audit Monthly Stock Report"** and click **Install**.

---

## Usage

1. Open the **Inventory** app.
2. Navigate to **Reporting → Inventory Stock Report (Excel)**.
3. The wizard opens:
   - Select one or more **Warehouses** (leave blank = all).
   - Select specific **Locations** (leave blank = all internal).
   - Select **Product Categories** (leave blank = all).
   - Tick **Include Zero-Stock Products** if needed.
4. Click **Generate Report** — the Excel file appears in the *Download* section.
5. Click the file field to download the `.xlsx` file.

---

## Excel Report Structure

### Sheet 1 — Summary
- Report title and generation timestamp
- Active filter summary
- **KPI Cards**: Total Products · Total Locations · Total Qty On Hand
- **Top 10 Products** table sorted by quantity

### Sheet 2 — Stock by Location
Columns: `Warehouse | Location | Product Code | Product Name | Category |
Lot/Serial | Package | Qty On Hand | UoM`

- Rows grouped under a **location sub-header**
- **Location subtotal** after each group
- **Grand Total** row at the bottom
- Frozen header row for easy scrolling

---

## File Structure
```
audit_monthly_stock_report/
├── __init__.py
├── __manifest__.py
├── security/
│   └── ir.model.access.csv
├── wizard/
│   ├── __init__.py
│   ├── audit_stock_report_wizard.py   ← Core logic & Excel builder
│   └── audit_stock_report_wizard_views.xml
└── static/description/
    └── index.html
```

---

## Compatibility
- **Odoo**: 18.0
- **Python**: 3.10+
- **openpyxl**: 3.1+
- **License**: LGPL-3
