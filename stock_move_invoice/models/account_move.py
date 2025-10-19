from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    picking_id = fields.Many2one('stock.picking', string='Picking')
    custom_form_date = fields.Datetime(string='Customs Form Date')

    @api.onchange('l10n_my_edi_display_tax_exemption_reason')
    def onchange_l10n_my_edi_tax_exemption_reason(self):
        if self.l10n_my_edi_display_tax_exemption_reason and self.l10n_my_edi_display_tax_exemption_reason == True:
            self.l10n_my_edi_exemption_reason = 'Licensed Manufacturing Warehouse (LMW)'

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    position_no = fields.Integer("Position")
