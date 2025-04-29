{
    'name': 'Import Stock Valuation',
    'version': '18.0',
    'category': 'stock',
    'author':'PPTS [India] Pvt.Ltd.',
    'description': """This module is for to import the records in stock valuation layer""",
    'depends': ['base_setup','stock','stock_account'],
    'website': 'https://www.pptssolutions.com',
    'data': [
        'security/ir.model.access.csv',
       # 'wizard/import_stock_valuation_view.xml',
    ],
    'installable': True,
    'application': True,
    'license':'LGPL-3',
    'sequence': 10,
}
