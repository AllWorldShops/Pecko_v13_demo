# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime

class Partner(models.Model):
    _inherit = 'res.partner'
    
    activity_date_deadline = fields.Datetime('')
    message_last_post = fields.Datetime('')
    commercial_partner_country_id = fields.Many2one('res.country', related='commercial_partner_id.country_id')
    opt_out = fields.Boolean('Opt-Out', help="If opt-out is checked, this contact has refused to receive emails for mass mailing and marketing campaign." "Filter 'Available for Mass Mailing' allows users to filter the partners when performing mass mailing.")
    has_address = fields.Boolean(string='Is address valid', readonly=True, store=True)
    x_studio_field_cH3lX = fields.Char('')
    x_studio_field_cpiWw = fields.Char('')
    x_studio_field_MTmaF = fields.Selection([('PEI', 'PEI'),('PKS', 'PKS'),('PM','PM'),('Avill','Avill')],string='Verification Status')