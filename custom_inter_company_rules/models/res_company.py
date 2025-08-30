# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, SUPERUSER_ID


class res_company(models.Model):
    _inherit = 'res.company'

    allowed_company_ids = fields.Many2many('res.company','m2m_res_company', 'header_id', 'company_id', string="Allowed Companies")
    