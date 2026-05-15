{
    'name': 'Customer/Partner Statement Report',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Generate customer and supplier invoice statement reports.',

    'description': """
This module helps generate customer and supplier invoice due statement reports.
It provides statement reports for partners/customers with invoice and due details.
""",

    'author': 'Point Perfect Technology Solutions',
    'company': 'Point Perfect Technology Solutions',

    'depends': [
        'base',
        'account',
        'contacts',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'wizard/partner_invoice_statement_views.xml',
    ],

    'images': [
        'static/description/banner.png',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}