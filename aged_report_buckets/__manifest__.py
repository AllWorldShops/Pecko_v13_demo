# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Bucket Calculation',
    'version': '1.0',
    'summary': 'Bucket Calculation',
    'description': 'This module is to round the invoice (decimal amount) to the nearest value for Customer Invoice and Vendor Bills',
    'category': 'Accounting',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': "www.pptssolutions.com",
    'company': 'PPTS INDIA PVT LTD',
    'depends': ['base', 'account','sale'],
    'data': [
        'views/res_config_settings_views.xml',
        'wizard/bucket_days_wizard.xml'
    ],
    'images': [ 
        
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
