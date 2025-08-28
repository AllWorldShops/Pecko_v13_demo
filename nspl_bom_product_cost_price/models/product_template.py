from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    default_bom_id = fields.Many2one(
        'mrp.bom',
        string="BoM",
        domain="[('product_tmpl_id', '=', id)]"
    )
    default_bom_cost = fields.Float(
        string="BoM Cost",
        compute="_compute_default_bom_cost",
        store=True
    )

    @api.depends('default_bom_id.total_bom_cost')
    def _compute_default_bom_cost(self):
        for rec in self:
            rec.default_bom_cost = rec.default_bom_id.total_bom_cost or 0.0
