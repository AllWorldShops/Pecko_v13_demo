# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'PPTS: Minimum purchase quantity based on Vendor',
    'version': '18.0',
    'category': 'Purchase',
    'summary': 'Quantity of "Buy" products will be based on minimum quantity for the vendor.',
    'description': """ This module has customizations for Purchase order generated from Sales/Manufacturing. """,
    "author": "PPTS [India] Pvt.Ltd.",
    'website': 'https://www.pptssolutions.com',
    'depends': ['base', 'purchase_stock'],

    'demo': [ ],
    'installable'   : True,
    'auto_install'  : False,
    'license'       : 'LGPL-3',
}