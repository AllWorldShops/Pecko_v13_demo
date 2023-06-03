{
    'name': 'Custom Fields ',
    'version': '16.0',
    'category': 'stock',
    'sequence':1,
    'summary': 'product customing to odoo16',
    'description': """This module contains pecko product customs odoo16.""",
    'depends': [
        'base_setup', 'product', 'stock','base','uom','mrp','account','account_followup','contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/studio_custom_fields.xml',

    ],
    'installable': True,
    'auto-install': False,
    'license': 'LGPL-3',
    'application': True,
}
