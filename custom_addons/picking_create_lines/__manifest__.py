# Copyright 2013 Nicolas Bessi (Camptocamp SA)
# Copyright 2014 Agile Business Group (<http://www.agilebg.com>)
# Copyright 2015 Grupo ESOC (<http://www.grupoesoc.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Picking Create lines groups",
    "summary": "Added groups for picking create lines",
    "version": "18.0.1.0.1",
    "author": "PPTS [India] Pvt.Ltd.",
    "license": "AGPL-3",
    "maintainer": "PPTS [India] Pvt.Ltd.",
    "category": "Extra Tools",
    "website": "https://www.pptssolutions.com",
    "depends": ["web","stock"],
    "data": [
        'security/ir.model.access.csv',
        'security/picking_create_security.xml',
        'data/action_server_create_category.xml',
        'views/partner_category_product_view_report.xml',
        'wizards/view_partner_category_product.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'picking_create_lines/static/src/js/picking_add_line_show.js',
        ]
    },
    
    'installable': True,
    'application': True,
    'auto_install': False,
}
