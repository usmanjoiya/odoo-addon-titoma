#!/usr/bin/env python3
# -*- coding: utf-8 -*-
{
    'name': "Customization - Titoma - Order Templates",
    'summary': 'Print order by Titoma Template',
    'author': "RichSoda",
    'maintainer': 'RichSoda <service@richsoda.com>',
    'website': "https://richsoda.com",
    'category': 'Sale',
    'version': '15.0.1.0.1',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'purchase',
        'account',
    ],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "qweb": [
    ],
    'data': [
        'views/report_templates.xml',
        'views/res_company_view.xml',
        'views/sale_report_views.xml',
        'views/purchase_report_views.xml',
        'views/invoice_report_views.xml',
    ],
    'demo': [
    ],
    'images': [],
    'application': False,
    'auto_install': False,
    'assets': {
        'web.report_assets_common': [
            'custom_titoma_templates/static/src/scss/titoma_report.scss',
        ],
    },
    'installable': True,
}
