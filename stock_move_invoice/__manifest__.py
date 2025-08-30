{
    'name': "Invoice From Stock Picking",
    'version': '18.0.1.0.0',
    'summary': """This module facilitates creating customer invoices & customer
                  credit notes automatically from stock picking.""",
    'description': """This module facilitates creating customer invoices & customer
                  credit notes automatically from stock picking..""",
    'category': 'Inventory',
    'depends': ['stock', 'account', 'sale'],
    'data': [
        'views/account_move_inherited.xml',
        'views/stock_picking_inherited.xml',
        'wizard/picking_invoice_wizard.xml',
    ],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
    'auto_install': False,
}

