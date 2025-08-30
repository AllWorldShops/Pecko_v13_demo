# -*- coding: utf-8 -*-

{
    'name': 'Custom Product',
    'version': '18.0.1.0.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Inventory/Product',
    'summary': 'Enhancements in the Product module for Odoo 18',
    'description': """This module provides enhancements to the Product module, including additional features for manufacturing and stock management.""",
    'depends': [
        'product',
        'mrp',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        # As there is Procurement Group Cron available by default.
        'data/stock_sequence_data.xml',
        'views/product_manufacturer_view.xml',
        'views/product_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
