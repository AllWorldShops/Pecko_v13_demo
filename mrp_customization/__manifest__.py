# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Workorder QR Code',
    'version': '13.0',
    'category': 'MRP',
    'author': 'PPTS',
    'sequence': 15,
    'summary': 'QR Code for task creation to pecko portal',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_view.xml',
        'views/mrp_url_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
