# -*- coding: utf-8 -*-

{
    'name': 'Custom Sale Order',
    'version': '13.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'sale',
    'description': """Enhancement in sale module""",
    'depends': ['base','sale_management','sales_team','account_reports'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
