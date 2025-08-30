{
    'name': 'Master Production Replenish Hide',
    'version': '18.0',
    'category': 'Manufacturing/Manufacturing',
    'sequence': 50,
    'summary': 'Master Production Replenish Hide',
    'depends': ['base_import', 'mrp', 'purchase_stock', 'mrp_mps', 'stock'],
    'description': """
Master Production Replenish Hide
""",
    'data': [
        'views/res_company_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'master_production_replenish_hide/static/src/components/replenish_hide.xml',
            'master_production_replenish_hide/static/src/components/replenish_line_view.xml',
        ],

    }
}
