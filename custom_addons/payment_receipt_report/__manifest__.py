# -*- coding: utf-8 -*-
{
    'name': 'PPTS Payment Receipt Report',
    'version': '18.0.1.0.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Accounting/Reports',
    'summary': 'Generate and manage payment receipt reports.',
    'description': """This module provides a customizable and detailed payment receipt report, enhancing financial reporting capabilities in the Accounting module.""",
    'depends': ['account', 'account_followup'],
    'data': [
        'report/report_payment_templates.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

