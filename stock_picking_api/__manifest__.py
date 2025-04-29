# -*- coding: utf-8 -*-

{
    'name': "Stock Picking API",

    'description': """
        Passing values to URl""",

    'category': 'Extra Tools',
    'version': '18.0.1.0.0',
    'license': "AGPL-3",

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/driver_master_view.xml',
        # 'views/stock_view.xml'
        
    ],
    'installable': True,
    'application': True
}
