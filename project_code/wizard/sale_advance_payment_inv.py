#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sale_advance_payment_inv.py

A module to extend the functionality of sale.advance.payment.inv to include project
code and project stage. This module inherits the sale.advance.payment.inv model and
adds two fields, project code and project stage, to the invoice created in the sale
order. The module overwrites the method _prepare_invoice_values to include the
values of the project code and project stage from the sale order in the created
invoice.
"""

import logging

import odoo
from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class SaleAdvancePaymentInv(models.TransientModel):
    """
    SaleAdvancePaymentInv
    A model class that inherits the sale.advance.payment.inv model. Adds the fields
    project_code and project_stage to the model. Overwrites the method
    _prepare_invoice_values to include the values of project code and project stage
    from the sale order in the created invoice.
    """

    _inherit = 'sale.advance.payment.inv'

    project_code = fields.Many2one('project.code', string='Project Code', help='Select a project code.')
    project_stage = fields.Selection([('D', 'D'), ('M', 'M'), ('P', 'P')], string='Project Stage', help='Select a project stage.')

    @api.model
    def _prepare_invoice_values(self, order, name, amount, so_line):
        invoice_vals = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(
            order, name, amount, so_line
        )
        invoice_vals['project_code'] = order.project_code.id
        invoice_vals['project_stage'] = order.project_stage
        return invoice_vals
