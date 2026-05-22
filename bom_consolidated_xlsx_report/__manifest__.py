{
    'name': 'BOM Consolidated XLSX Report',
    'version': '18.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Generate consolidated BOM XLSX reports with quantity and stock details.',

    'description': """
BOM Consolidated XLSX Report
============================

This module helps generate consolidated BOM reports in XLSX format.

Features:
---------
* Generate consolidated BOM reports
* Merge duplicate raw materials automatically
* Calculate total required quantity based on BOM quantity
* Display stock availability details
* Show incoming and outgoing quantities
* Export reports in Excel (XLSX) format
""",

    'author': 'Point Perfect Technology Solutions',
    'company': 'Point Perfect Technology Solutions',

    'depends': [
        'base',
        'mrp',
    ],

    'data': [
        'security/ir.model.access.csv',
        'wizard/bom_consolidated_xlsx_views.xml',
        'views/mrp_bom_views.xml',
    ],

    'images': [
        'static/description/banner.png',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}