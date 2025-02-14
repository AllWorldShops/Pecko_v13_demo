# -*- coding: utf-8 -*-

{
    'name': 'Custom MRP',
    'version': '18.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Manufacturing',
    'description': """Manufacturing lines split""",
    'depends': ['mrp', 'stock', 'base','sale','custom_product'],
    'data': [
        'security/button_return_access_group_view.xml',
        'views/mrp_line.xml',
        'views/decimal_data.xml',
        'views/res_config_view.xml',
        'report/custom_mrp_inherit.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    "assets": {
        "web.assets_backend": [
        'custom_mrp/static/src/components/inherit_bom_overview_table/mrp_bom_display_filter.js',
        'custom_mrp/static/src/components/inherit_bom_overview_table/mrp_inherit_bom_overview_table.xml',
        'custom_mrp/static/src/components/inherit_bom_overview_table/mrp_custom_base.xml',
        ]
    },
}