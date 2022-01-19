# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from xmlrpc.client import boolean
# from odoo.tools.func import default
from odoo.addons.web_editor.models.ir_qweb import Integer


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    days_count = fields.Integer(string='Bucket Days Count')
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res.update(
            days_count=int(ICPSudo.get_param('aged_report_buckets.days_count')),
        )
        return res

    # @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("aged_report_buckets.days_count", self.days_count)
