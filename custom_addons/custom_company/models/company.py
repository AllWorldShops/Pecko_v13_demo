# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _

class Company(models.Model):
    _inherit = "res.company"
    
    fax = fields.Char('Fax')
    street1 = fields.Char('Street 1')

        
