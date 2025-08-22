# -*- coding: utf-8 -*-
{
    'name': "stock_val_layer_curr_val_diff_patch",
    'category': 'Uncategorized',
    'version': '0.1',
    'summary': 'This module has customizations for the stock rule',
    'description': """ This module has customizations for the stock rule. """,
    "author": "PPTS [India] Pvt.Ltd.",
    'website': 'www.pptssolutions.com',
    'depends': ['base','product','stock', 'stock_account'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
