# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'custom fields',
    'version': '1.1',
    'summary': 'Custom Studio fields',
    'website': 'https://www.pptssolutions.com',
    'depends': ['product', 'stock','base','uom','mrp','account'],
    'category': 'stock',
    'sequence': 13,
    'description': """
custom fields from studio
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/studio_custom_fields_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
