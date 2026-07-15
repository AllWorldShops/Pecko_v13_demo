from odoo import models,fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    is_pecko_usd = fields.Boolean(string="Is Pecko USD?")
    trading_type = fields.Selection([('traders','Traders'),('non_traders','Non-Traders'),('transport','Transport')],string="Trading Type", tracking=True)

class ResCompany(models.Model):
    _inherit = "res.company"

    is_aws_company = fields.Boolean(string="Is AWS Company?")