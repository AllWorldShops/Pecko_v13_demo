# -*- coding: utf-8 -*-

{
    'name': 'Custom Purchase',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Purchase',
    'description': """Enhancement in Purchase module""",
    'depends': ['purchase','custom_product'],
    'data': [
        'views/purchase_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
