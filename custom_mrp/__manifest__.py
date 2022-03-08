# -*- coding: utf-8 -*-

{
    'name': 'Custom MRP',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Manufacturing',
    'description': """Manufacturing lines split""",
    'depends': ['mrp','stock','base','custom_product','sale'],
    'data': [
        'views/mrp_line.xml',
        'views/decimal_data.xml',
        'views/res_config_view.xml',
        'report/bom_structure.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
