{
    'name': 'BOM Product Cost Price',
    'version': '16.0',
    'summary': 'Show cost price of BoM product and total BoM cost',
    'description': """
    Display cost price of the product defined in the Bill of Materials (BoM) and the total cost of all components.

    ✔ View BoM component cost and total cost  
    ✔ Improve production cost transparency  
    ✔ Assist in pricing and margin calculations
    """,
    'category': 'Manufacturing',
    'sequence': 4,
    'author': 'Namah Softech Private Limited',
    'website': 'https://www.nspl.com',
    'license': 'LGPL-3',
    'support': 'support@namahsoftech.com',
    'price': 19.99,
    'currency': 'USD',
    'contributors': ['Shivani Solanki'],
    'depends': ['mrp', 'product','sale'],
    'data': [
        'views/mrp_bom_views.xml',
        'views/product_views.xml',
    ],
    'images': ['static/description/img/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
