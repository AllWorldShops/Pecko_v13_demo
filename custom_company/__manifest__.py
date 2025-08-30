# -*- coding: utf-8 -*-
{
    'name': 'Custom Company',
    'version': '18.0.1.0.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Customizations/Company',
    'summary': 'Enhancements to the base module for company management.',
    'description': """This module adds fields to the company master and done enhancements to the mail model""",
    'depends': ['base', 'mail'],
    'data': [
        'views/company_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
