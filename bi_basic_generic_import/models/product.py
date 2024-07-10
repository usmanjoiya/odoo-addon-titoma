# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import tempfile
import binascii
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, exceptions, api, _
import time
from datetime import date, datetime
import io
import logging

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')
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


class ProductTemplate(models.Model):
    """
    Add manufacturer code

    [product.template]
    """

    _inherit = "product.template"

    manufacturer_code = fields.Char(string='Manufacturer Code', compute='_compute_manufacturer_code', inverse='_set_manufacturer_code', store=True)

    @api.depends('product_variant_ids', 'product_variant_ids.manufacturer_code')
    def _compute_manufacturer_code(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.manufacturer_code = template.product_variant_ids.manufacturer_code
        for template in (self - unique_variants):
            template.manufacturer_code = False

    def _set_manufacturer_code(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.manufacturer_code = template.manufacturer_code


class ProductProduct(models.Model):
    """
    Add manufacturer code

    [product.product]
    """

    _inherit = "product.product"

    manufacturer_code = fields.Char(string='Manufacturer Code')


class gen_product(models.TransientModel):
    _name = "gen.product"

    file = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select', default='csv')
    product_option = fields.Selection([('create', 'Create Product'),
                                       ('update', 'Update Product')], string='Option', required=True, default="create")
    product_search = fields.Selection([('by_code', 'Search By Code'), ('by_name', 'Search By Name'),
                                       ('by_barcode', 'Search By Barcode')], string='Search Product')
    file_name = fields.Char()

    def create_product(self, values):
        product_obj = self.env['product.product']
        product_categ_obj = self.env['product.category']
        product_uom_obj = self.env['uom.uom']
        product_tax = self.env['account.tax']
        if values.get('categ_id') == '':
            raise ValidationError(_('CATEGORY field can not be empty'))
        else:
            categ_id = product_categ_obj.search([('name', '=', values.get('categ_id'))], limit=1)

        if values.get('type') == 'Consumable':
            categ_type = 'consu'
        elif values.get('type') == 'Service':
            categ_type = 'service'
        elif values.get('type') == 'Storable Product':
            categ_type = 'product'
        else:
            categ_type = 'product'

        if values.get('uom_id') == '':
            uom_id = 1
        else:
            uom_search_id = product_uom_obj.search([('name', '=', values.get('uom_id'))], limit=1)
            uom_id = uom_search_id.id

        if values.get('uom_po_id') == '':
            uom_po_id = 1
        else:
            uom_po_search_id = product_uom_obj.search([('name', '=', values.get('uom_po_id'))], limit=1)
            uom_po_id = uom_po_search_id.id
        if values.get('barcode') == '':
            barcode = False
        else:
            barcode = values.get('barcode')

        if values.get('customer_texes') == '':
            taxes_id = False
        else:
            customer_texes_search_id = product_tax.search([
                ('name', '=', values.get('customer_texes')),
                ('type_tax_use', '=', 'sale')], limit=1)
            if customer_texes_search_id:
                taxes_id = [(6, 0, customer_texes_search_id.ids)]
            else:
                taxes_id = False

        if values.get('vendor_taxes') == '':
            supplier_taxes_id = False
        else:
            vendor_taxes_search_id = product_tax.search([
                ('name', '=', values.get('vendor_taxes')),
                ('type_tax_use', '=', 'purchase')], limit=1)
            if vendor_taxes_search_id:
                supplier_taxes_id = [(6, 0, vendor_taxes_search_id.ids)]
            else:
                supplier_taxes_id = False

        if values.get('routes') == 'Manufacture':
            route_ids = self.env.ref('mrp.route_warehouse0_manufacture')
        else:
            route_ids = self.env.ref('purchase_stock.route_warehouse0_buy')

        if str(values.get('mto')) != '' and str(values.get('mto')).upper() == 'YES':
            route_ids += self.env.ref('stock.route_warehouse0_mto')

        vals = {
            'name': values.get('name'),
            'default_code': values.get('default_code'),
            'manufacturer_code': values.get('manufacturer_code'),
            'categ_id': categ_id[0].id,
            'type': categ_type,
            'barcode': barcode,
            'uom_id': uom_id,
            'uom_po_id': uom_po_id,
            'lst_price': values.get('sale_price'),
            'standard_price': values.get('cost_price'),
            'weight': values.get('weight'),
            'volume': values.get('volume'),
            'taxes_id': taxes_id,
            'supplier_taxes_id': supplier_taxes_id,
            'hs_code': values.get('hs_code'),
            'route_ids': [(6, 0, route_ids.ids)]
        }

        res = product_obj.create(vals)

        # Product Suppler
        seller_ids = self.get_product_suppler(values)
        if seller_ids:
            seller_ids['product_id'] = res.id
            res.write({'seller_ids': [(0, 0, seller_ids)]})

        # Reorder Rule
        stock_orderpoint_vals = self.get_reorder_rule(values, categ_type)
        if stock_orderpoint_vals:
            stock_orderpoint_vals['product_id'] = res.id
            self.env['stock.warehouse.orderpoint'].create(stock_orderpoint_vals)

        return res

    def import_product(self):

        if not self.file:
            raise ValidationError(_('Please select the file.'))

        if self.import_option == 'csv':
            if self.file:
                file_name = str(self.file_name)
                extension = file_name.split('.')[1]
            if extension not in ['csv', 'CSV']:
                raise ValidationError(_('Please upload only csv file.!'))
            keys = ['name', 'default_code', 'manufacturer_code', 'categ_id', 'type', 'barcode', 'uom_id', 'uom_po_id', 'sale_price', 'cost_price', 'weight', 'volume',
                    'vendor_name', 'vendor_product_code', 'currency_id', 'min_qty', 'purchase_price', 'customer_taxes', 'vendor_taxes', 'hs_code', 'routes', 'mto',
                    'product_min_qty', 'product_max_qty']
            csv_data = base64.b64decode(self.file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            file_reader = []
            res = {}
            csv_reader = csv.reader(data_file, delimiter=',')

            try:
                file_reader.extend(csv_reader)
            except Exception:
                raise ValidationError(_("Invalid file!"))
            values = {}
            for i in range(len(file_reader)):
                field = map(str, file_reader[i])
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        values.update({'option': self.import_option})
                        if self.product_option == 'create':
                            res = self.create_product(values)
                        else:
                            product_obj = self.env['product.product']
                            product_categ_obj = self.env['product.category']
                            product_uom_obj = self.env['uom.uom']
                            product_tax = self.env['account.tax']
                            categ_id = False
                            categ_type = False
                            barcode = False
                            uom_id = False
                            uom_po_id = False
                            taxes_id = False
                            supplier_taxes_id = False
                            if values.get('categ_id') == '':
                                pass
                            else:
                                categ_id = product_categ_obj.search([('name', '=', values.get('categ_id'))], limit=1)
                                if not categ_id:
                                    raise ValidationError('CATEGORY field can not be empty')

                            if values.get('type') == '':
                                pass
                            else:
                                if values.get('type') == 'Consumable':
                                    categ_type = 'consu'
                                elif values.get('type') == 'Service':
                                    categ_type = 'service'
                                elif values.get('type') == 'Storable Product':
                                    categ_type = 'product'
                                else:
                                    categ_type = 'product'

                            if values.get('barcode') == '':
                                pass
                            else:
                                barcode = values.get('barcode')

                            if values.get('uom_id') == '':
                                pass
                            else:
                                uom_search_id = product_uom_obj.search([('name', '=', values.get('uom_id'))], limit=1)
                                if not uom_search_id:
                                    raise ValidationError(_('UOM field can not be empty'))
                                else:
                                    uom_id = uom_search_id.id

                            if values.get('uom_po_id') == '':
                                pass
                            else:
                                uom_po_search_id = product_uom_obj.search([('name', '=', values.get('uom_po_id'))], limit=1)
                                if not uom_po_search_id:
                                    raise ValidationError(_('Purchase UOM field can not be empty'))
                                else:
                                    uom_po_id = uom_po_search_id.id

                            if values.get('customer_texes') == '':
                                pass
                            else:
                                customer_texes_search_id = product_tax.search([
                                    ('name', '=', values.get('customer_texes')),
                                    ('type_tax_use', '=', 'sale')], limit=1)
                                taxes_id = customer_texes_search_id.ids

                            if values.get('vendor_taxes') == '':
                                pass
                            else:
                                vendor_taxes_search_id = product_tax.search([('name', '=', values.get('vendor_taxes')),
                                                                             ('type_tax_use', '=', 'purchase')], limit=1)
                                supplier_taxes_id = vendor_taxes_search_id.ids

                            if values.get('routes') == 'Manufacture':
                                route_ids = self.env.ref('mrp.route_warehouse0_manufacture')
                            else:
                                route_ids = self.env.ref('purchase_stock.route_warehouse0_buy')

                            if str(values.get('mto')) != '' and str(values.get('mto')).upper() == 'YES':
                                route_ids += self.env.ref('stock.route_warehouse0_mto')

                            # Product Suppler
                            seller_ids = self.get_product_suppler(values)

                            # Reorder Rule
                            stock_orderpoint_vals = self.get_reorder_rule(values, categ_type)

                            if self.product_search == 'by_code':
                                product_ids = self.env['product.product'].search([('default_code', '=', values.get('default_code'))], limit=1)
                                if product_ids:
                                    if values.get('manufacturer_code'):
                                        product_ids.write({'manufacturer_code': values.get('manufacturer_code') or False})
                                    if categ_id:
                                        product_ids.write({'categ_id': categ_id[0].id or False})
                                    if categ_type:
                                        product_ids.write({'type': categ_type or False})
                                    if barcode and product_ids.barcode != barcode:
                                        product_ids.write({'barcode': barcode or False})
                                    if uom_id:
                                        product_ids.write({'uom_id': uom_id or False})
                                    if uom_po_id:
                                        product_ids.write({'uom_po_id': uom_po_id})
                                    if values.get('sale_price'):
                                        product_ids.write({'lst_price': values.get('sale_price') or False})
                                    if values.get('cost_price'):
                                        product_ids.write({'standard_price': values.get('cost_price') or False})
                                    if values.get('weight'):
                                        product_ids.write({'weight': values.get('weight') or False})
                                    if values.get('volume'):
                                        product_ids.write({'volume': values.get('volume') or False})
                                    if values.get('hs_code'):
                                        product_ids.write({'hs_code': values.get('hs_code') or False})
                                    if taxes_id:
                                        product_ids.write({'taxes_id': [(6, 0, taxes_id)] or False})
                                    if supplier_taxes_id:
                                        product_ids.write({'supplier_taxes_id': [(6, 0, supplier_taxes_id)] or False})
                                    if route_ids:
                                        product_ids.write({'route_ids': [(6, 0, route_ids.ids)] or False})
                                    if seller_ids:
                                        match_seller = product_ids.seller_ids.filtered(lambda r: r.name.id == seller_ids['name'])
                                        if match_seller:
                                            match_seller[:1].write(seller_ids)
                                        else:
                                            seller_ids['product_id'] = product_ids.id
                                            product_ids.write({'seller_ids': [(0, 0, seller_ids)]})
                                    if product_ids.type == 'product' and stock_orderpoint_vals:
                                        reorder_rule = self.env['stock.warehouse.orderpoint'].search([
                                            ('product_id', '=', product_ids.id),
                                            ('location_id', '=', stock_orderpoint_vals['location_id'])], limit=1)
                                        stock_orderpoint_vals['product_id'] = product_ids.id
                                        if reorder_rule:
                                            reorder_rule.write(stock_orderpoint_vals)
                                        else:
                                            reorder_rule.create(stock_orderpoint_vals)
                                else:
                                    raise UserError(_('"%s" Product not found.') % values.get('default_code'))
                            elif self.product_search == 'by_name':
                                product_ids = self.env['product.product'].search([('name', '=', values.get('name'))], limit=1)
                                if product_ids:
                                    if values.get('manufacturer_code'):
                                        product_ids.write({'manufacturer_code': values.get('manufacturer_code') or False})
                                    if categ_id:
                                        product_ids.write({'categ_id': categ_id[0].id or False})
                                    if categ_type:
                                        product_ids.write({'type': categ_type or False})
                                    if barcode and product_ids.barcode != barcode:
                                        product_ids.write({'barcode': barcode or False})
                                    if uom_id:
                                        product_ids.write({'uom_id': uom_id or False})
                                    if uom_po_id:
                                        product_ids.write({'uom_po_id': uom_po_id})
                                    if values.get('sale_price'):
                                        product_ids.write({'lst_price': values.get('sale_price') or False})
                                    if values.get('cost_price'):
                                        product_ids.write({'standard_price': values.get('cost_price') or False})
                                    if values.get('weight'):
                                        product_ids.write({'weight': values.get('weight') or False})
                                    if values.get('volume'):
                                        product_ids.write({'volume': values.get('volume') or False})
                                    if values.get('hs_code'):
                                        product_ids.write({'hs_code': values.get('hs_code') or False})
                                    if taxes_id:
                                        product_ids.write({'taxes_id': [(6, 0, taxes_id)] or False})
                                    if supplier_taxes_id:
                                        product_ids.write({'supplier_taxes_id': [(6, 0, supplier_taxes_id)] or False})
                                    if route_ids:
                                        product_ids.write({'route_ids': [(6, 0, route_ids.ids)] or False})
                                    if seller_ids:
                                        match_seller = product_ids.seller_ids.filtered(lambda r: r.name.id == seller_ids['name'])
                                        if match_seller:
                                            match_seller[:1].write(seller_ids)
                                        else:
                                            seller_ids['product_id'] = product_ids.id
                                            product_ids.write({'seller_ids': [(0, 0, seller_ids)]})
                                    if product_ids.type == 'product' and stock_orderpoint_vals:
                                        reorder_rule = self.env['stock.warehouse.orderpoint'].search([
                                            ('product_id', '=', product_ids.id),
                                            ('location_id', '=', stock_orderpoint_vals['location_id'])], limit=1)
                                        stock_orderpoint_vals['product_id'] = product_ids.id
                                        if reorder_rule:
                                            reorder_rule.write(stock_orderpoint_vals)
                                        else:
                                            reorder_rule.create(stock_orderpoint_vals)
                                else:
                                    raise ValidationError(_('%s product not found.') % values.get('name'))
                            else:
                                product_ids = self.env['product.product'].search([('barcode', '=', values.get('barcode'))])
                                if product_ids:
                                    if values.get('manufacturer_code'):
                                        product_ids.write({'manufacturer_code': values.get('manufacturer_code') or False})
                                    if categ_id != False:
                                        product_ids.write({'categ_id': categ_id[0].id or False})
                                    if categ_type != False:
                                        product_ids.write({'type': categ_type or False})
                                    if uom_id != False:
                                        product_ids.write({'uom_id': uom_id or False})
                                    if uom_po_id != False:
                                        product_ids.write({'uom_po_id': uom_po_id})
                                    if values.get('sale_price'):
                                        product_ids.write({'lst_price': values.get('sale_price') or False})
                                    if values.get('cost_price'):
                                        product_ids.write({'standard_price': values.get('cost_price') or False})
                                    if values.get('weight'):
                                        product_ids.write({'weight': values.get('weight') or False})
                                    if values.get('volume'):
                                        product_ids.write({'volume': values.get('volume') or False})
                                    if values.get('hs_code'):
                                        product_ids.write({'hs_code': values.get('hs_code') or False})
                                    if taxes_id:
                                        product_ids.write({'taxes_id': [(6, 0, taxes_id)] or False})
                                    if supplier_taxes_id:
                                        product_ids.write({'supplier_taxes_id': [(6, 0, supplier_taxes_id)] or False})
                                    if route_ids:
                                        product_ids.write({'route_ids': [(6, 0, route_ids.ids)] or False})
                                    if seller_ids:
                                        match_seller = product_ids.seller_ids.filtered(lambda r: r.name.id == seller_ids['name'])
                                        if match_seller:
                                            match_seller[:1].write(seller_ids)
                                        else:
                                            seller_ids['product_id'] = product_ids.id
                                            product_ids.write({'seller_ids': [(0, 0, seller_ids)]})
                                    if product_ids.type == 'product' and stock_orderpoint_vals:
                                        reorder_rule = self.env['stock.warehouse.orderpoint'].search([
                                            ('product_id', '=', product_ids.id),
                                            ('location_id', '=', stock_orderpoint_vals['location_id'])], limit=1)
                                        stock_orderpoint_vals['product_id'] = product_ids.id
                                        if reorder_rule:
                                            reorder_rule.write(stock_orderpoint_vals)
                                        else:
                                            reorder_rule.create(stock_orderpoint_vals)
                                else:
                                    raise ValidationError(_('%s product not found.') % values.get('barcode'))
        else:
            if self.file:
                file_name = str(self.file_name)
                extension = file_name.split('.')[1]
            if extension not in ['xls', 'xlsx', 'XLS', 'XLSX']:
                raise ValidationError(_('Please upload only xls file.!'))
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            res = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = list(map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    keys = ['name', 'default_code', 'manufacturer_code', 'categ_id', 'type', 'barcode', 'uom_id', 'uom_po_id', 'sale_price', 'cost_price', 'weight', 'volume',
                            'vendor_name', 'vendor_product_code', 'currency_id', 'min_qty', 'purchase_price', 'customer_taxes', 'vendor_taxes', 'hs_code', 'routes', 'mto',
                            'product_min_qty', 'product_max_qty', ]
                    values = dict(zip(keys, line))
                    if self.product_option == 'create':
                        res = self.create_product(values)
                    else:
                        product_obj = self.env['product.product']
                        product_categ_obj = self.env['product.category']
                        product_uom_obj = self.env['uom.uom']
                        product_tax = self.env['account.tax']
                        categ_id = False
                        categ_type = False
                        barcode = False
                        uom_id = False
                        uom_po_id = False
                        taxes_id = False
                        supplier_taxes_id = False
                        if values.get('categ_id') == '':
                            pass
                        else:
                            categ_id = product_categ_obj.search([('name', '=', values.get('categ_id'))], limit=1)
                            if not categ_id:
                                raise ValidationError('CATEGORY field can not be empty')

                        if values.get('type') == '':
                            pass
                        else:
                            if values.get('type') == 'Consumable':
                                categ_type = 'consu'
                            elif values.get('type') == 'Service':
                                categ_type = 'service'
                            elif values.get('type') == 'Storable Product':
                                categ_type = 'product'
                            else:
                                categ_type = 'product'

                        if values.get('barcode') == '':
                            pass
                        else:
                            barcode = values.get('barcode')

                        if values.get('uom_id') == '':
                            pass
                        else:
                            uom_search_id = product_uom_obj.search([('name', '=', values.get('uom_id'))], limit=1)
                            if not uom_search_id:
                                raise ValidationError(_('UOM field can not be empty'))
                            else:
                                uom_id = uom_search_id.id

                        if values.get('uom_po_id') == '':
                            pass
                        else:
                            uom_po_search_id = product_uom_obj.search([('name', '=', values.get('uom_po_id'))], limit=1)
                            if not uom_po_search_id:
                                raise ValidationError(_('Purchase UOM field can not be empty'))
                            else:
                                uom_po_id = uom_po_search_id.id

                        if values.get('customer_texes') == '':
                            pass
                        else:
                            customer_texes_search_id = product_tax.search([
                                ('name', '=', values.get('customer_texes')),
                                 ('type_tax_use', '=', 'sale')], limit=1)
                            taxes_id = customer_texes_search_id.ids

                        if values.get('vendor_taxes') == '':
                            pass
                        else:
                            vendor_taxes_search_id = product_tax.search([('name', '=', values.get('vendor_taxes')),
                                                                         ('type_tax_use', '=', 'purchase')], limit=1)
                            supplier_taxes_id = vendor_taxes_search_id.ids

                        if values.get('routes') == 'Manufacture':
                            route_ids = self.env.ref('mrp.route_warehouse0_manufacture')
                        else:
                            route_ids = self.env.ref('purchase_stock.route_warehouse0_buy')

                        if str(values.get('mto')) != '' and str(values.get('mto')).upper() == 'YES':
                            route_ids += self.env.ref('stock.route_warehouse0_mto')

                        # Product Suppler
                        seller_ids = self.get_product_suppler(values)

                        # Reorder Rule
                        stock_orderpoint_vals = self.get_reorder_rule(values, categ_type)

                        if self.product_search == 'by_code':
                            product_ids = self.env['product.product'].search([('default_code', '=', values.get('default_code'))], limit=1)
                            if product_ids:
                                if values.get('manufacturer_code'):
                                    product_ids.write({'manufacturer_code': values.get('manufacturer_code') or False})
                                if categ_id:
                                    product_ids.write({'categ_id': categ_id[0].id or False})
                                if categ_type:
                                    product_ids.write({'type': categ_type or False})
                                if barcode and product_ids.barcode != barcode:
                                    product_ids.write({'barcode': barcode or False})
                                if uom_id:
                                    product_ids.write({'uom_id': uom_id or False})
                                if uom_po_id:
                                    product_ids.write({'uom_po_id': uom_po_id})
                                if values.get('sale_price'):
                                    product_ids.write({'lst_price': values.get('sale_price') or False})
                                if values.get('cost_price'):
                                    product_ids.write({'standard_price': values.get('cost_price') or False})
                                if values.get('weight'):
                                    product_ids.write({'weight': values.get('weight') or False})
                                if values.get('volume'):
                                    product_ids.write({'volume': values.get('volume') or False})
                                if values.get('hs_code'):
                                    product_ids.write({'hs_code': values.get('hs_code') or False})
                                if taxes_id:
                                    product_ids.write({'taxes_id': [(6, 0, taxes_id)] or False})
                                if supplier_taxes_id:
                                    product_ids.write({'supplier_taxes_id': [(6, 0, supplier_taxes_id)] or False})
                                if route_ids:
                                    product_ids.write({'route_ids': [(6, 0, route_ids.ids)] or False})
                                if seller_ids:
                                    match_seller = product_ids.seller_ids.filtered(lambda r: r.name.id == seller_ids['name'])
                                    if match_seller:
                                        match_seller[:1].write(seller_ids)
                                    else:
                                        seller_ids['product_id'] = product_ids.id
                                        product_ids.write({'seller_ids': [(0, 0, seller_ids)]})
                                if product_ids.type == 'product' and stock_orderpoint_vals:
                                    reorder_rule = self.env['stock.warehouse.orderpoint'].search([
                                        ('product_id', '=', product_ids.id),
                                        ('location_id', '=', stock_orderpoint_vals['location_id'])], limit=1)
                                    stock_orderpoint_vals['product_id'] = product_ids.id
                                    if reorder_rule:
                                        reorder_rule.write(stock_orderpoint_vals)
                                    else:
                                        reorder_rule.create(stock_orderpoint_vals)
                            else:
                                raise UserError(_('"%s" Product not found.') % values.get('default_code'))
                        elif self.product_search == 'by_name':
                            product_ids = self.env['product.product'].search([('name', '=', values.get('name'))], limit=1)
                            if product_ids:
                                if values.get('manufacturer_code'):
                                    product_ids.write({'manufacturer_code': values.get('manufacturer_code') or False})
                                if categ_id:
                                    product_ids.write({'categ_id': categ_id[0].id or False})
                                if categ_type:
                                    product_ids.write({'type': categ_type or False})
                                if barcode and product_ids.barcode != barcode:
                                    product_ids.write({'barcode': barcode or False})
                                if uom_id:
                                    product_ids.write({'uom_id': uom_id or False})
                                if uom_po_id:
                                    product_ids.write({'uom_po_id': uom_po_id})
                                if values.get('sale_price'):
                                    product_ids.write({'lst_price': values.get('sale_price') or False})
                                if values.get('cost_price'):
                                    product_ids.write({'standard_price': values.get('cost_price') or False})
                                if values.get('weight'):
                                    product_ids.write({'weight': values.get('weight') or False})
                                if values.get('volume'):
                                    product_ids.write({'volume': values.get('volume') or False})
                                if values.get('hs_code'):
                                    product_ids.write({'hs_code': values.get('hs_code') or False})
                                if taxes_id:
                                    product_ids.write({'taxes_id': [(6, 0, taxes_id)] or False})
                                if supplier_taxes_id:
                                    product_ids.write({'supplier_taxes_id': [(6, 0, supplier_taxes_id)] or False})
                                if route_ids:
                                    product_ids.write({'route_ids': [(6, 0, route_ids.ids)] or False})
                                if seller_ids:
                                    match_seller = product_ids.seller_ids.filtered(lambda r: r.name.id == seller_ids['name'])
                                    if match_seller:
                                        match_seller[:1].write(seller_ids)
                                    else:
                                        seller_ids['product_id'] = product_ids.id
                                        product_ids.write({'seller_ids': [(0, 0, seller_ids)]})
                                if product_ids.type == 'product' and stock_orderpoint_vals:
                                    reorder_rule = self.env['stock.warehouse.orderpoint'].search([
                                        ('product_id', '=', product_ids.id),
                                        ('location_id', '=', stock_orderpoint_vals['location_id'])], limit=1)
                                    stock_orderpoint_vals['product_id'] = product_ids.id
                                    if reorder_rule:
                                        reorder_rule.write(stock_orderpoint_vals)
                                    else:
                                        reorder_rule.create(stock_orderpoint_vals)
                            else:
                                raise ValidationError(_('%s product not found.') % values.get('name'))
                        else:
                            product_ids = self.env['product.product'].search([('barcode', '=', values.get('barcode'))], limit=1)
                            if product_ids:
                                if values.get('manufacturer_code'):
                                    product_ids.write({'manufacturer_code': values.get('manufacturer_code') or False})
                                if categ_id != False:
                                    product_ids.write({'categ_id': categ_id[0].id or False})
                                if categ_type != False:
                                    product_ids.write({'type': categ_type or False})
                                if uom_id != False:
                                    product_ids.write({'uom_id': uom_id or False})
                                if uom_po_id != False:
                                    product_ids.write({'uom_po_id': uom_po_id})
                                if values.get('sale_price'):
                                    product_ids.write({'lst_price': values.get('sale_price') or False})
                                if values.get('cost_price'):
                                    product_ids.write({'standard_price': values.get('cost_price') or False})
                                if values.get('weight'):
                                    product_ids.write({'weight': values.get('weight') or False})
                                if values.get('volume'):
                                    product_ids.write({'volume': values.get('volume') or False})
                                if values.get('hs_code'):
                                    product_ids.write({'hs_code': values.get('hs_code') or False})
                                if taxes_id:
                                    product_ids.write({'taxes_id': [(6, 0, taxes_id)] or False})
                                if supplier_taxes_id:
                                    product_ids.write({'supplier_taxes_id': [(6, 0, supplier_taxes_id)] or False})
                                if route_ids:
                                    product_ids.write({'route_ids': [(6, 0, route_ids.ids)] or False})
                                if seller_ids:
                                    match_seller = product_ids.seller_ids.filtered(lambda r: r.name.id == seller_ids['name'])
                                    if match_seller:
                                        match_seller[:1].write(seller_ids)
                                    else:
                                        seller_ids['product_id'] = product_ids.id
                                        product_ids.write({'seller_ids': [(0, 0, seller_ids)]})
                                if product_ids.type == 'product' and stock_orderpoint_vals:
                                    reorder_rule = self.env['stock.warehouse.orderpoint'].search([
                                        ('product_id', '=', product_ids.id),
                                        ('location_id', '=', stock_orderpoint_vals['location_id'])], limit=1)
                                    stock_orderpoint_vals['product_id'] = product_ids.id
                                    if reorder_rule:
                                        reorder_rule.write(stock_orderpoint_vals)
                                    else:
                                        reorder_rule.create(stock_orderpoint_vals)
                            else:
                                raise ValidationError(_('%s product not found.') % values.get('barcode'))
        return res

    def get_reorder_rule(self, values, categ_type):
        """
        Get reorder rule values

        :param values: Dict for row values
        :param categ_type: Product type
        :return: Dict for reorder rule
        """

        product_min_qty = values.get('product_min_qty')
        product_max_qty = values.get('product_max_qty')
        if categ_type == 'product' and product_min_qty and product_max_qty:
            try:
                product_min_qty = float(product_min_qty)
            except TypeError:
                raise ValidationError(_('Min Quantity must be number'))

            try:
                float(product_max_qty)
            except TypeError:
                raise ValidationError(_('Max Quantity must be number'))

            company_warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)])
            stock_orderpoint_vals = {
                'location_id': company_warehouse[:1].lot_stock_id.id,
                'product_min_qty': product_min_qty,
                'product_max_qty': product_max_qty,
                'qty_multiple': 1,
            }
        else:
            stock_orderpoint_vals = False

        return stock_orderpoint_vals

    def get_product_suppler(self, values):
        """
        Get product suppler

        :param values: Dict for row values
        :param categ_type: Product type
        :return: Dict for product suppler values
        """

        vendor_name = values.get('vendor_name')
        currency = values.get('currency_id')
        min_qty = values.get('min_qty')
        purchase_price = values.get('purchase_price')
        if vendor_name and currency and min_qty and purchase_price:
            if vendor_name == '':
                raise ValidationError(_('Vendor Name field can not be empty'))
            else:
                partner_search_id = self.env['res.partner'].search([('name', '=', values.get('vendor_name'))], limit=1)
                if partner_search_id:
                    partner_id = partner_search_id.id
                else:
                    partner_id = partner_search_id.create({
                        'name': values.get('vendor_name'),
                        'is_company': True,
                    })

            if currency == '':
                raise ValidationError(_('Currency field can not be empty'))
            else:
                currency_search_id = self.env['res.currency'].search([('name', '=', currency)], limit=1)
                currency_id = currency_search_id.id

            try:
                min_qty = float(min_qty)
            except ValueError:
                raise ValidationError(_('Quantity must be number'))

            try:
                purchase_price = float(purchase_price)
            except ValueError:
                raise ValidationError(_('Price must be number'))

            seller_ids = {
                'name': partner_id,
                'product_code': values.get('vendor_product_code'),
                'currency_id': currency_id,
                'min_qty': min_qty,
                'price': purchase_price,
                'delay': 1,
            }
        else:
            seller_ids = False

        return seller_ids
