{
    'name': 'Delivery Quantity',
    'version': '16.0',
    'category': 'stock',
    'sequence':1,
    'summary': 'product customing to odoo16',
    'description': """This module contains pecko product customs odoo16.""",
    'depends': ['base','stock','sale'],
    'data': ['views/quantity_done.xml'],
    'installable': True,
    'auto-install': False,
    'license': 'LGPL-3',
    'application': True,
}
