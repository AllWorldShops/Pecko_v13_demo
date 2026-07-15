{
    "name": "PPTS Monthly Sales Purchase Report",
    "summary": "PPTS Monthly Sales Purchase Report",
    "version": "18.0.1.0.1",
    "author": "PPTS [India] Pvt.Ltd.",
    "license": "AGPL-3",
    "maintainer": "PPTS [India] Pvt.Ltd.",
    "category": "Extra Tools",
    "website": "https://www.pptssolutions.com",
    "depends": ["account", "base"],
    "data": [
        'security/ir.model.access.csv',
        'views/financial_year_views.xml',
        'wizard/monthly_sales_report_views.xml',
        'wizard/monthly_purchase_report_views.xml',
        'views/account_journal_inherit_views.xml',
        'views/res_partner_inherit.xml',

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
