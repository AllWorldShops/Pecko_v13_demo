# -*- coding: utf-8 -*-

{
    'name': 'Invoice Credit Notes',
    'version': '16.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Account',
    'description': """Invoice Credit Notes""",
    'depends': ['account', 'base_setup'],
    'data': [
        'views/invoice_action.xml',
        'views/menuitem.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
