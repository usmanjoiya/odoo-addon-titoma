#!/usr/bin/env python3
# -*- coding: utf-8 -*-
{
    'name': "Project Code",
    "summary": "增加專案代號及階段於 S/O, P/O, M/O, invoice, picking PDF 。",
    "author": "RichSoda",
    "maintainer": "RichSoda <service@richsoda.com>",
    "website": "https://richsoda.com",
    "category": "Base",
    "version": "15.0.0.0.4",
    "license": "AGPL-3",
    "depends": [
        "mrp",
        "sale_stock",
        "purchase_stock",
        ],

    "external_dependencies": {
        "python": [],
        "bin": [],
        },
    "qweb": [
    ],
    "data": [
        "views/account_invoice_template.xml",
        "views/account_move_view.xml",
        "views/mrp.report_mrporder_template.xml",
        "views/mrp_production_view.xml",
        "views/project_code_views.xml",
        "views/purchase_order_view.xml",
        "views/purchase_template.xml",
        "views/report_saleorder.template.xml",
        "views/sales_order_view.xml",
        "views/stock_picking_template.xml",
        "views/stock_picking_view.xml",
        "security/ir.model.access.csv",
    ],
    'demo': [
    ],
    "application": False,
    "auto_install": False,
    "installable": True,
}
