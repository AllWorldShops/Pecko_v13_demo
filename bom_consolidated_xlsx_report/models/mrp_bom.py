from odoo import models, fields, api, _

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    # Open the BOM Consolidated wizard
    def action_open_bom_consolidated_wizard(self):
        return {
                'type': 'ir.actions.act_window',
                'name': 'BOM Consolidated Report',
                'res_model': 'bom.consolidated.report',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_bom_id': self.id,'default_company_id':self.env.company.id
                }
            }

    