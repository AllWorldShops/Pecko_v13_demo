# -*- coding: utf-8 -*-

{
    'name': 'Log activity in Stock',
    'version': '18.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Inventory',
    'description': """Log activity for stock modules""",
    'depends': ['stock', 'base'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/log_activity_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}