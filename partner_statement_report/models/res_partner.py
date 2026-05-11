import base64
import io
import json
import xlsxwriter
from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools.json import json_default


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Open the Partner Statement wizard 11-05-2026
    def action_open_statement_wizard(self):
        return {
                'type': 'ir.actions.act_window',
                'name': 'Partner Statement',
                'res_model': 'partner.invoice.statement',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_partner_id': self.id,'default_company_id':self.env.company.id
                }
            }

   