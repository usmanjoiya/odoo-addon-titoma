#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
res_company.py

Titoma Company Bank Info
"""
import logging

from odoo import models, api, fields, _, exceptions

_logger = logging.getLogger(__name__)


class Company(models.Model):
    """
    Titoma Company Bank Info

    [res.company]
    """

    _inherit = 'res.company'

    bank_info = fields.Html(string='Bank Information', copy=False)
