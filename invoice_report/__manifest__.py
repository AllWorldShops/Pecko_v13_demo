# -*- coding: utf-8 -*-

{
    'name': 'Invoice Report',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Account',
    'description': """Invoice Report""",
    'depends': ['web', 'account', 'account_followup'],
    'data': [
        'report/account_invoice_report.xml',
        'report/account_invoice_report_templates.xml',
        # 'report/follow-up_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
