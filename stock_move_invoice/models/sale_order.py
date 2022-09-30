from odoo import fields, models, api, _

class SalesOrder(models.Model):
    _inherit = 'sale.order.line'

    # invoiced_qty = fields.Float('Invoiced Qty')

    # @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'qty_delivered')
    # def _get_invoice_qty(self):
    #     """
    #     Compute the quantity invoiced. If case of a refund, the quantity invoiced is decreased. Note
    #     that this is the case only if the refund is generated from the SO and that is intentional: if
    #     a refund made would automatically decrease the invoiced quantity, then there is a risk of reinvoicing
    #     it automatically, which may not be wanted at all. That's why the refund has to be created from the SO
    #     """
    #     for line in self:
    #         qty_invoiced = 0.0
    #         if line.invoice_lines:
    #             for invoice_line in line.invoice_lines:
    #                 if invoice_line.move_id.state != 'cancel':
    #                     if invoice_line.move_id.type == 'out_invoice':
    #                         qty_invoiced += invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
    #                     elif invoice_line.move_id.type == 'out_refund':
    #                         qty_invoiced -= invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
                
    #             # line.qty_invoiced = qty_invoiced
    #         if not line.invoice_lines:
    #             stock_move_qty = sum(self.env['stock.move'].search([('sale_line_id', '=', line.id),('product_id', '=', line.product_id.id),('picking_id.invoice_created','=', True)]).mapped('quantity_done'))
    #             qty_invoiced = stock_move_qty
    #         line.qty_invoiced = qty_invoiced