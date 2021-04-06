# -*- coding: utf-8 -*-

{
    'name': 'Custom Product',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Product',
    'description': """Enhancement in Product module""",
    'depends': ['product','mrp','stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_sequence_data.xml',
        'views/product_manufacturer_view.xml',
        'views/product_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
