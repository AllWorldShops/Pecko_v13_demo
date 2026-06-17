from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    purchase_order_line_limit = fields.Integer(string="PO Line Limit",help="Defines the maximum number of lines allowed in a purchase order. When this limit is exceeded, a new purchase order will be created.")

    