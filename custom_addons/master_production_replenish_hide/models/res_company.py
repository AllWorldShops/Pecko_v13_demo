from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    location_ids = fields.Many2many("stock.location", string="Location")
