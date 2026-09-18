{
    'name': 'Restrict DO & Invoice Delete',
    'version': '18.0.1.0.0',
    'summary': 'Per-company toggle to restrict who can delete Delivery Orders and Invoices',
    'category': 'Operations/Inventory',
    'author': 'Point Perfect Technology Solutions',
    'company': 'Point Perfect Technology Solutions',
    'depends': ['stock', 'account', 'base'],
    'data': [
        'security/ir_rule_data.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
}
