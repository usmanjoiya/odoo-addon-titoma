#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stock_picking.py
List Project Code and Project Stage in AccountMove.
"""
import logging

import odoo
from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """
    Account Move
    This class inherits the 'account.move' model in Odoo and adds two new fields to it:
    project_code and project_stage. project_code is a many2one field to the
    project_code model, and project_stage is a selection field with three options:
    D, M, and P.

    [account.move]
    """

    _inherit = 'account.move'

    project_code = fields.Many2one('project.code', string='Project Code', help='Select a project code.')
    project_stage = fields.Selection([('D', 'D'), ('M', 'M'), ('P', 'P')], string='Project Stage', help='Select a project stage.')
