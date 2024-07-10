#!/usr/bin/env python3
# -*- coding: utf-8 -*-
{
    'name': "Unique Internal Reference",
    'summary': 'Unique Internal reference for product',
    'description': """
Unique Internal Reference
=========================
**Unique Internal reference for product**

*By RichSoda Co., Ltd., Odoo Taiwan. <service@richsoda.com> https://richsoda.com*

This is a module for a web-based opensource business suite, [Odoo](http://odoo.com/).

This module help user restricted the internal reference of product must be unique.

Features
--------
* Support Odoo v15
* Product
    - Restricted the internal reference must be unique
    
Usage
-----
1. Install from the Odoo "App" menu

Contact
-------
If you have any question or advice, please email us at service@richsoda.com or visit our website, https://richsoda.com
    """,
    'author': "RichSoda",
    'maintainer': 'RichSoda <service@richsoda.com>',
    'website': "https://richsoda.com",
    'category': 'Product',
    'version': '15.0.0.1',
    'license': 'AGPL-3',
    'depends': [
        'product',
    ],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "qweb": [
    ],
    'data': [
    ],
    'demo': [
    ],
    'images': [],
    'application': False,
    'auto_install': False,
    'installable': True,
}
