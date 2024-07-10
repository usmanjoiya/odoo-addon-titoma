# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning, ValidationError
from odoo import models, fields, exceptions, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from xlrd import open_workbook
import os
import tempfile
import binascii
from xlwt import Workbook
import logging

_logger = logging.getLogger(__name__)
from io import StringIO
import io

try:
    import xmlrpclib
except ImportError:
    _logger.debug('Cannot `import xmlrpclib`.')

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')


class gen_inv(models.TransientModel):
    _name = "gen.inv"

    file = fields.Binary('File')
    inv_name = fields.Char('Inventory Name')
    import_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select', default='csv')
    import_prod_option = fields.Selection([('barcode', 'Barcode'), ('code', 'Code'), ('name', 'Name')],
        string='Import Product By ', default='code')
    lot_option = fields.Boolean(string="Import Serial/Lot number with Expiry Date")
    file_name = fields.Char()

    def make_inventory_date(self, date):
        DATETIME_FORMAT = "%Y-%m-%d"
        if date:
            try:
                i_date = datetime.strptime(date, DATETIME_FORMAT).date()
            except Exception:
                raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
            return i_date
        else:
            raise ValidationError(_('Date field is blank in sheet Please add the date.'))

    def import_csv(self):

        """Load Inventory data from the CSV file."""
        if self.import_option == 'csv':
            """Load Inventory data from the CSV file."""
            try:
                if self.lot_option == True:
                    keys = ['location_id', 'product_tmpl', 'quantity', 'in_date', 'UOM', 'lot']
                else:
                    keys = ['location_id', 'product_tmpl', 'quantity', 'in_date', 'UOM']
                product_obj = self.env['product.product']
                stock_lot_obj = self.env['stock.production.lot']
                csv_data = base64.b64decode(self.file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                file_reader = []
                csv_reader = csv.reader(data_file, delimiter=',')
                file_reader.extend(csv_reader)
            except Exception:
                raise ValidationError(_("Invalid file!"))
            values = {}
            product_list = []
            stock_quant_id = False
            for i in range(len(file_reader)):
                val = {}
                try:
                    field = list(map(str, file_reader[i]))
                except ValueError:
                    raise ValidationError(_("Don't Use Character only use numbers"))

                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        if self.import_prod_option == 'barcode':
                            prod_lst = product_obj.search([('barcode', '=', values['product_tmpl'])], limit=1)
                            if not prod_lst:
                                raise UserError(
                                    _('"%s" Product Barcode is not available.') % (values['product_tmpl']))

                        elif self.import_prod_option == 'code':
                            prod_lst = product_obj.search([('default_code', '=', values['product_tmpl'])], limit=1)
                            if not prod_lst:
                                raise UserError(_('"%s" Product Code is not available.') % (values['product_tmpl']))

                        else:
                            prod_lst = product_obj.search([('name', '=', values['product_tmpl'])], limit=1)

                        if prod_lst.id:
                            product_list.append(prod_lst.id)
                        if self.lot_option == True:
                            if prod_lst:
                                val['product_tmpl'] = prod_lst[0].id
                                val['location_id'] = values['location_id']
                                val['lot'] = values['lot']
                                val['in_date'] = values['in_date']
                                val['product_uom_id'] = values['UOM']
                            if bool(val):
                                product_uom_obj = self.env['uom.uom']
                                product_uom_id = product_uom_obj.search([('name', '=', val['product_uom_id'])])
                                if not product_uom_id:
                                    raise UserError(
                                        _('"%s" Product UOM category is not available.') % (val['product_uom_id']))
                                lot_id = stock_lot_obj.search(
                                    [('product_id', '=', val['product_tmpl']), ('name', '=', val['lot'])])
                                if not lot_id:
                                    date_exp = self.make_inventory_date(val['in_date'])
                                    lot = stock_lot_obj.create({'name': val['lot'],
                                                                'product_id': val['product_tmpl'],
                                                                'expiration_date': date_exp,
                                                                'company_id': self.env.user.company_id.id})
                                    lot_id = lot
                                stock_location_id = self.env['stock.location'].search(
                                    [('complete_name', '=', values['location_id'])])
                                uom_id = self.env['uom.uom'].search(
                                    [('name', '=', values['UOM'])])
                                # stock quant create
                                stock_quant_id = self.env['stock.quant'].create(
                                    {
                                        'in_date': values['in_date'],
                                        'product_id': prod_lst[0].id,
                                        'inventory_quantity': values['quantity'],
                                        'lot_id': lot_id.id,
                                        'location_id': stock_location_id.id,
                                        'company_id': self.env.user.company_id.id,
                                        'product_uom_id': uom_id.id,
                                        'is_import': True
                                    })
                                stock_quant_id.sudo().action_apply_inventory()
                            else:
                                continue
                        else:
                            if prod_lst:
                                val['product_tmpl'] = prod_lst[0].id
                                val['location_id'] = values['location_id']
                                val['quantity'] = values['quantity']
                                val['uom_id'] = values['UOM']
                                val['in_date'] = values['in_date']
                            if bool(val):
                                product_uom_obj = self.env['uom.uom']
                                product_uom_id = product_uom_obj.search([('name', '=', val['uom_id'])])
                                if not product_uom_id:
                                    raise UserError(
                                        _('"%s" Product UOM category is not available.') % (val['uom_id']))
                                stock_location_id = self.env['stock.location'].search(
                                    [('complete_name', '=', values['location_id'])])
                                uom_id = self.env['uom.uom'].search(
                                    [('name', '=', values['UOM'])])

                                # stock quant create
                                stock_quant_id = self.env['stock.quant'].create(
                                    {
                                        'in_date': values['in_date'],
                                        'product_id': prod_lst[0].id,
                                        'inventory_quantity': values['quantity'],
                                        'location_id': stock_location_id.id,
                                        'company_id': self.env.user.company_id.id,
                                        'product_uom_id': uom_id.id,
                                        'is_import': True
                                    })
                                stock_quant_id.sudo().action_apply_inventory()
                            else:
                                continue
            return stock_quant_id
        else:
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                values = {}
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise ValidationError(_("Invalid file!"))
            product_obj = self.env['product.product']
            stock_lot_obj = self.env['stock.production.lot']
            product_list = []
            stock_quant_id = False

            for row_no in range(sheet.nrows):

                val = {}
                if row_no <= 0:
                    fields = list(map(lambda row: row.value.encode('utf-8'), sheet.row(row_no)))
                else:
                    line = list(
                        map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(
                            row.value),
                            sheet.row(row_no)))

                    if self.lot_option == True:
                        if line:
                            if len(line) < 6:
                                raise ValidationError(_("Please add columns properly!"))
                            values.update({
                                'location_id': line[0],
                                'product_tmpl': line[1],
                                'quantity': line[2],
                                'UOM': line[3],
                                'in_date': line[4],
                                'lot': line[5]})
                            if line[4] != '':
                                if line[4].split('/'):
                                    if len(line[4].split('/')) > 1:
                                        raise ValidationError(
                                            _('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
                                    if len(line[4]) > 10 or len(line[4]) < 5:
                                        raise ValidationError(
                                            _('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
                            a1 = int(float(line[4]))
                            a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                            date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                            if self.import_prod_option == 'barcode':
                                res = values['product_tmpl'].replace('.', '', 1).isdigit()
                                if res == True:
                                    prod_lst = product_obj.search(
                                        [('barcode', '=', int(float(values['product_tmpl'])))],
                                        limit=1)
                                else:
                                    prod_lst = product_obj.search([('barcode', '=', values['product_tmpl'])],
                                        limit=1)

                                if not prod_lst:
                                    raise UserError(
                                        _('"%s" Product Barcode is not available.') % (values['product_tmpl']))
                            elif self.import_prod_option == 'code':
                                res = values['product_tmpl'].replace('.', '', 1).isdigit()
                                if res == True:
                                    prod_lst = product_obj.search(
                                        [('default_code', '=', int(float(values['product_tmpl'])))], limit=1)
                                else:
                                    prod_lst = product_obj.search([('default_code', '=', values['product_tmpl'])],
                                        limit=1)

                                if not prod_lst:
                                    raise UserError(
                                        _('"%s" Product Code is not available.') % (values['product_tmpl']))
                            else:
                                prod_lst = product_obj.search([('name', '=', values['product_tmpl'])], limit=1)
                            if prod_lst:
                                if prod_lst:
                                    val['product_tmpl'] = prod_lst[0].id
                                    val['location_id'] = values['location_id']
                                    val['lot'] = values['lot']
                                    val['in_date'] = date_string
                                    val['product_uom_id'] = values['UOM']
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name', '=', val['product_uom_id'])])
                                    if not product_uom_id:
                                        raise UserError(
                                            _('"%s" Product UOM category is not available.') % (
                                                val['product_uom_id']))
                                    stock_location_id = self.env['stock.location'].search(
                                        [('complete_name', '=', values['location_id'])])
                                    uom_id = self.env['uom.uom'].search(
                                        [('name', '=', values['UOM'])])
                                    lot_id = stock_lot_obj.search(
                                        [('product_id', '=', val['product_tmpl']), ('name', '=', val['lot'])])
                                    if not lot_id:
                                        date_exp = self.make_inventory_date(val['in_date'])
                                        lot = stock_lot_obj.create({'name': val['lot'],
                                                                    'product_id': val['product_tmpl'],
                                                                    'expiration_date': date_exp,
                                                                    'company_id': self.env.user.company_id.id})
                                        lot_id = lot
                                    # stock quant create
                                    stock_quant_id = self.env['stock.quant'].create(
                                        {
                                            'in_date': date_string,
                                            'product_id': prod_lst[0].id,
                                            'inventory_quantity': values['quantity'],
                                            'location_id': stock_location_id.id,
                                            'company_id': self.env.user.company_id.id,
                                            'lot_id': lot_id.id,
                                            'product_uom_id': uom_id.id,
                                            'is_import': True
                                        })
                                    stock_quant_id.sudo().action_apply_inventory()

                            else:
                                continue

                    else:
                        if line:
                            values.update({
                                'location_id': line[0],
                                'product_tmpl': line[1],
                                'quantity': line[2],
                                'UOM': line[3],
                                'in_date': line[4],
                            })
                            if line[4] != '':
                                if line[4].split('/'):
                                    if len(line[4].split('/')) > 1:
                                        raise ValidationError(
                                            _('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
                                    if len(line[4]) > 8 or len(line[4]) < 5:
                                        raise ValidationError(
                                            _('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
                            a1 = int(float(line[4]))
                            a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                            date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                            if self.import_prod_option == 'barcode':
                                res = values['product_tmpl'].replace('.', '', 1).isdigit()
                                if res == True:
                                    prod_lst = product_obj.search(
                                        [('barcode', '=', int(float(values['product_tmpl'])))],
                                        limit=1)
                                else:
                                    prod_lst = product_obj.search([('barcode', '=', values['product_tmpl'])],
                                        limit=1)

                                if not prod_lst:
                                    raise UserError(
                                        _('"%s" Product Barcode is not available.') % (values['product_tmpl']))
                            elif self.import_prod_option == 'code':
                                res = values['product_tmpl'].replace('.', '', 1).isdigit()
                                if res == True:
                                    prod_lst = product_obj.search(
                                        [('default_code', '=', int(float(values['product_tmpl'])))], limit=1)
                                else:
                                    prod_lst = product_obj.search([('default_code', '=', values['product_tmpl'])],
                                        limit=1)

                                if not prod_lst:
                                    raise UserError(
                                        _('"%s" Product Code is not available.') % (values['product_tmpl']))
                            else:
                                prod_lst = product_obj.search([('name', '=', values['product_tmpl'])], limit=1)
                            if prod_lst:
                                if prod_lst:
                                    val['product_tmpl'] = prod_lst[0].id
                                    val['location_id'] = values['location_id'],
                                    val['in_date'] = date_string,
                                    val['product_uom_id'] = values['UOM'],
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name', '=', val['product_uom_id'])])
                                    if not product_uom_id:
                                        raise UserError(
                                            _('"%s" Product UOM category is not available.') % (
                                                val['product_uom_id']))
                                    stock_location_id = self.env['stock.location'].search(
                                        [('complete_name', '=', values['location_id'])])
                                    uom_id = self.env['uom.uom'].search(
                                        [('name', '=', values['UOM'])])

                                    # stock quant create
                                    stock_quant_id = self.env['stock.quant'].create(
                                        {
                                            'in_date': date_string,
                                            'product_id': prod_lst[0].id,
                                            'inventory_quantity': values['quantity'],
                                            'location_id': stock_location_id.id,
                                            'company_id': self.env.user.company_id.id,
                                            'product_uom_id': uom_id.id,
                                            'is_import': True,
                                        })
                                    stock_quant_id.sudo().action_apply_inventory()
                            else:
                                continue

        return stock_quant_id

    class StockQuant(models.Model):
        _inherit = "stock.quant"

        is_import = fields.Boolean(string=" Is Imported data", default=False)
