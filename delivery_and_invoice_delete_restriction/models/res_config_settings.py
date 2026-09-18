from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    restrict_do_invoice_delete = fields.Boolean(
        related='company_id.restrict_do_invoice_delete',
        readonly=False,
        string='Allow DO & Invoice Delete',
    )
    delete_allowed_user_ids = fields.Many2many(
        related='company_id.delete_allowed_user_ids',
        readonly=False,
        string='Users Allowed to Delete DO/Invoices',
    )
