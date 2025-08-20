# -*- coding: utf-8 -*-

{
    'name': 'Sales Details Report',
    'version': '16.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'sale',
    'description': """Sales Details Report""",
    'depends': ['base','sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sales_details_report_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
