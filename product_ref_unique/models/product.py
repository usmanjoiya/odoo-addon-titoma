#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
product.py

Unique default code for product
"""

from odoo import models


class ProductProduct(models.Model):
    """
    Unique default code for product

    [product.product]
    """

    _inherit = 'product.product'

    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code)', "Internal reference must be unique!"),
    ]
