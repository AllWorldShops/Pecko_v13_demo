{
    'name': 'Audit Monthly Stock Report',
    'version': '18.0.2.1.0',
    'category': 'Inventory/Reporting',
    'summary': 'Monthly stock Excel report with multi-company sheets and audit log',
    'description': """
        - Multi-company Excel report: one sheet per company
        - SG companies get RMA Delivery & RMA Receipt columns (before Total Valuation)
        - Total Valuation column (cost x qty on hand)
        - Grand totals for Raw Materials and Finished Goods
        - audit.monthly.report model stores every generated report
        - Daily cron checks if today is month-end and auto-generates the report
    """,
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'depends': ['stock', 'product', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/audit_monthly_report_views.xml',
        'data/cron.xml',
        # 'wizard/audit_stock_report_wizard_views.xml',
    ],
    # 'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
