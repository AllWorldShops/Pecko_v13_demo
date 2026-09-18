from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    restrict_do_invoice_delete = fields.Boolean(
        string='Allow DO & Invoice Delete',
        help=(
            'When enabled, users cannot delete Delivery Orders or Invoices  belonging to this company, except the users listed below.'
        ),
    )
    delete_allowed_user_ids = fields.Many2many(
        'res.users',
        'res_company_delete_allowed_users_rel',
        'company_id',
        'user_id',
        string='Users Allowed to Delete DO/Invoices',
        help='Only these users can delete Delivery Orders/Invoices when the restriction above is enabled.',
    )
