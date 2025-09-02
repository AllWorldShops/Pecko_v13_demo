from odoo import fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    picking_id = fields.Many2one('stock.picking', string='Picking')
    custom_form_date = fields.Datetime(string='Customs Form Date')

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    position_no = fields.Integer("Position")
