# -*- coding: utf-8 -*-

{
    'name': 'Custom Purchase',
    'version': '16.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Purchase',
    'description': """Enhancement in Purchase module""",
    'depends': ['purchase','custom_product','pecko_so_po_report', 'sale_purchase_inter_company_rules'],
    'data': [
        'views/purchase_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
