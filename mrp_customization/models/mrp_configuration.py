from odoo import fields, models, api

class UrlConfig(models.Model):
    _name = "url.config"
    _description = "url"
    
    name = fields.Char(string='URL',required=True)
    code = fields.Char(string='Code',required=True)