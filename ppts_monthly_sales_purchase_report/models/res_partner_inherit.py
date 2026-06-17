from odoo import models,fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    is_pecko_usd = fields.Boolean(string="Is Pecko USD?")