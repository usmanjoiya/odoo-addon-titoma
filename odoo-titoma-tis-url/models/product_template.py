from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tis_url = fields.Html(string='TIS URL', compute='_compute_tis_url')

    @api.depends('default_code')  # 'default_code' is the field for 'Internal Reference'
    def _compute_tis_url(self):
        base_url = "https://inventory.titoma.com/#/tpn/search/component/"
        for record in self:
            if record.default_code:
                full_url = '{}{}'.format(base_url, record.default_code)
                record.tis_url = '<a href="{}">{}</a>'.format(full_url, full_url)
            else:
                record.tis_url = False