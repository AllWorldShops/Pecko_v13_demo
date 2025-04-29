{
    "name": "Purchase order creation",
    "summary": "purchse order creation",
    'version': '18.0.1.0.0',
    "author": "PPTS",
    "license": "AGPL-3",

    "depends": ["purchase",'purchse_stock'],
    "data": [
      'data/service_cron.xml',
      'views/purchase_view.xml'
    ],
    "auto_install": False,
    "installable": True,
}
