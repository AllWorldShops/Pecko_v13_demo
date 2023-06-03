from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime,date


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


    active = fields.Boolean(default=True, help="Set active to false to hide the PurchaseOrder without removing it.")

    def _compute_active(self):
        records = self.search([('state', 'in', ('draft','sent')),('active','=',False)])
        for each in records:
            if each.date_order.strftime('%d-%m-%Y') <= date.today().strftime('%d-%m-%Y'):
                each.active =True
            else:
                each.active=False

        