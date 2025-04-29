# -*- coding: utf-8 -*-
{
    'name': 'Invoice Credit Notes',
    'version': '18.0.1.0.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Accounting',
    'summary': 'Manage and process invoice credit notes effectively.',
    'description': """This module provides functionality to handle and manage invoice credit notes seamlessly, enhancing the accounting operations.""",
    'depends': ['account', 'base_setup'],
    'data': [
        'views/invoice_action.xml',
        'views/menuitem.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
