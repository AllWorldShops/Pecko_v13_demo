{
    "name": "Purchase order creation",
    "summary": "purchse order creation",
    "version": "16.0.1.0.1",
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
