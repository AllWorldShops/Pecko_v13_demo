{
    'name': "Purchase Order Line Limit",

    'summary': "Limit the number of lines per Purchase Order and automatically split excess lines.",

    'description': """
            This module allows you to define a maximum number of lines for each Purchase Order.

            When the number of order lines exceeds the configured limit, the system will
            automatically create one or more additional Purchase Orders for the remaining lines.

            Key Features:
            - Configure maximum line limit at company level
            - Automatically split Purchase Orders when limit is exceeded
            - Maintain same vendor, currency, and company in split orders
            - Ensures better control and manageability of large Purchase Orders
            """,

    'author': "Vishnu Sasikumar",
    'category': 'Point of Sale',
    'version': '18.0.1.0.0',
    'depends': ['base','purchase'],

    'data': [
        'views/res_company_views.xml'
    ],

    # 'images': ['static/description/banner.png'],

    'license': "LGPL-3",
    'installable': True,
    'application': True,
    'auto_install': False,
}

