# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Partner Ledger Custom',
    'version': '18.0',
    'summary': 'Partner Ledger',
    'description': 'This module is to round the invoice (decimal amount) to the nearest value for Customer Invoice and Vendor Bills',
    'category': 'Accounting',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'company': 'PPTS INDIA PVT LTD',
    'depends': ['base', 'account','sale', 'account_reports'],
    'data': [
        'views/partner_ledger.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
