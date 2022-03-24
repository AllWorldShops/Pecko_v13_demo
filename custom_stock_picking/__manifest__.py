# -*- coding: utf-8 -*-

{
    'name': 'Custom Stock',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Stock',
    'description': """Enhancement in inventory module""",
    'depends': ['stock','account','sale_stock'],
    'data': [
        'views/stock_view.xml',
        'views/ac_move_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
