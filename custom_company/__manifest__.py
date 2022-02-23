# -*- coding: utf-8 -*-

{
    'name': 'Custom company',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Company',
    'description': """Enhancement in base module""",
    'depends': ['base', 'mail'],
    'data': [
        'views/company_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
