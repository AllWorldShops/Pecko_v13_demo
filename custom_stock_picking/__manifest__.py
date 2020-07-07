# -*- coding: utf-8 -*-

{
    'name': 'Custom Stock',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Stock',
    'description': """Enhancement in inventory module""",
    'depends': ['stock','sale_stock'],
    'data': [
        'views/stock_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
