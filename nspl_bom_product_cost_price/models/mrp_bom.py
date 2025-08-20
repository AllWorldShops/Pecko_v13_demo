from odoo import models, fields, api

class MrpBom(models.Model):
    _inherit = "mrp.bom"

    product_cost_price = fields.Float(
        string="Product Cost Price",
        related="product_tmpl_id.standard_price",
        readonly=True
    )

    total_bom_cost = fields.Float(
        string="Total BoM Cost", compute="_compute_total_bom_cost", store=True
    )

    @api.depends("bom_line_ids.product_id", "bom_line_ids.product_qty")
    def _compute_total_bom_cost(self):
        for bom in self:
            total = 0.0
            for line in bom.bom_line_ids:
                total += line.product_id.standard_price * line.product_qty
            bom.total_bom_cost = total


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    component_cost_price = fields.Float(
        string="Component Cost Price",
        related="product_id.standard_price",
        readonly=True
    )

# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'
    

#     bom_cost = fields.Float(string="BOM Cost")
#     bom_percentage = fields.Float(string="BOM(%)")

#     @api.onchange('product_template_id','price_unit')
#     def action_update_bom_cost(self):
#         for rec in self:
#             rec.bom_cost = 0.0
#             rec.bom_percentage = 0.0
#             if rec.product_template_id.bom_count >=1:
#                 mrp_bom = self.env['mrp.bom'].search([('product_tmpl_id','=',rec.product_template_id.id)],limit=1,order="id desc")
#                 if mrp_bom:
#                     if rec.currency_id.id == rec.company_id.currency_id.id:
#                         rec.bom_cost = mrp_bom.total_bom_cost 
#                         total_value = (rec.price_unit - rec.bom_cost)
#                         total_sum_value = (total_value / rec.bom_cost)*100
#                         rec.bom_percentage = total_sum_value
#                     else:
#                         rec.bom_cost = mrp_bom.total_bom_cost / rec.currency_id.inverse_rate
#                         total_value = (rec.price_unit - rec.bom_cost)
#                         total_sum_value = (total_value / rec.bom_cost)*100
#                         rec.bom_percentage = total_sum_value