# -*- coding: utf-8 -*-
{
    "name" : "Manual Currency Exchange Rate",
    "version" : "1.0",
    "depends" : ['base','account'],
    "author": "Asesora IT",
    "summaray" : 'Apply Manual Exchange Rate on Invoices and Register Payment.',
    "price": 0,    
    "currency": "USD",
    'category': 'Accounting',
    "website" : "",
    "data" :[
        "views/customer_invoice.xml",
        "views/account_payment_view.xml",
        ],
    #'qweb':[
    #],
    "auto_install": False,
    "installable": True,
    #'application': True,
    "images": ['static/description/icon.png'],
    "license": "LGPL-3",
}
