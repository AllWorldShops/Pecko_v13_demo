# -*- coding: utf-8 -*-

{
    'name': 'Custom MRP',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Manufacturing',
    'description': """Manufacturing lines split""",
    'depends': ['mrp','stock','custom_product'],
    'data': [
        'views/mrp_line.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
