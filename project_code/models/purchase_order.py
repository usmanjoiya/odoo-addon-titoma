#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
purchase_order.py
List Project Code and Project Stage in PurchaseOrder.
"""
import logging

import odoo
from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):

    """
    Purchase Order
    This class inherits the 'purchase.order' model in Odoo and adds two new fields to it:
    project_code and project_stage. project_code is a many2one field to the
    project_code model, and project_stage is a selection field with three options:
    D, M, and P. It also includes a method 'create_picking' that creates a stock
    picking for the purchase order and adds the project code and project stage to it. It
    also includes an override for the '_prepare_invoice' method to add the project
    code and project stage to the created invoice.

    [purchase.order]
    """

    _inherit = 'purchase.order'

    project_code = fields.Many2one('project.code', string='Project Code', help='Select a project code.')
    project_stage = fields.Selection([('D', 'D'), ('M', 'M'), ('P', 'P')], string='Project Stage', help='Select a project stage.')

    @api.model
    def _prepare_picking(self):
        """
        Prepare stock picking for purchase order

        Overrides the original '_prepare_picking' method to add the project code and
        project stage to the created stock picking. Returns the updated values.
        """
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({
            'project_code': self.project_code.id,
            'project_stage': self.project_stage
            })
        return res

    def _prepare_invoice(self):
        """
        Prepare invoice for purchase order

        Overrides the original '_prepare_invoice' method to add the project code and
        project stage to the created invoice. Returns the updated invoice values.
        """
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals['project_code'] = self.project_code.id
        invoice_vals['project_stage'] = self.project_stage
        return invoice_vals
