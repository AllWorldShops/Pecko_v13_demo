# -*- coding: utf-8 -*-

{
    'name': 'PPTS Payment Receipt Report',
    'version': '13.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Account',
    'description': """Payment Receipt Report""",
    'depends': ['account', 'account_followup'],
    'data': [
        # 'report/payment_receipt_report_templates.xml',
        'report/report_payment_templates.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
