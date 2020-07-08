# -*- coding: utf-8 -*-

{
    'name' : 'SO,PO Report',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Sale',
    'description': """Sale Order,Purchase Order PDF Report""",
    'depends' : ['base','sale','purchase','stock','account'],
    'data': [
        'views/so_po_order_view.xml',
        'views/report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application':True
}