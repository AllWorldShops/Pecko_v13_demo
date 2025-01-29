{
    'name': 'UOM Log Note',
    'summary': 'Displays log notes in the UOM (Unit of Measure) master',
    'version': '18.0.1.0.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'company': 'PPTS [India] Pvt.Ltd.',
    'category': 'Inventory/Configuration',
    'description': """This module enables the display of log notes in the UOM (Unit of Measure) master for better tracking and documentation.""",
    'depends': [
        'base',
        'sale_management',
        'stock',
        'uom',
    ],
    'data': [
        'views/uom_log_note.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}




