#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stock_picking.py
List Project Code and Project Stage in StockPicking.
"""
import logging

import odoo
from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    project_code = fields.Many2one('project.code', string='Project Code', help='Select a project code.')
    project_stage = fields.Selection([('D', 'D'), ('M', 'M'), ('P', 'P')], string='Project Stage', help='Select a project stage.')
