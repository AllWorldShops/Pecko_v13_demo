from odoo import fields, models, api

class UrlConfig(models.Model):
    _name = "url.config"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "url"
    
    name = fields.Char(string='URL',required=True, tracking=True)
    code = fields.Char(string='Code',required=True, tracking=True)
    active = fields.Boolean("Active", default=True)