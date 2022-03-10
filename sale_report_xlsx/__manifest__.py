# -*- coding: utf-8 -*-
# This file is part of OpenERP. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
{
    'name' : 'Sale Order Excel Report',
    'version': '13.0',
    'category': 'Stock',
    'website': 'https://www.pptssolutions.com',
    'license': 'LGPL-3',

    'depends': [
        'sale','base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_order_xls_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
