# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _

class SaleOrder(models.Model):   
    _inherit = "sale.order"
    
    attn = fields.Many2one('res.partner',string="ATTN")
    customer_po_no = fields.Char(string="Customer PO No")
    origin = fields.Char(string='Order Ref No', help="Reference of the document that generated this sales order request.")
    effective_date = fields.Date("Effective Date", compute='_compute_effective_date', store=True, help="Completion date of the first delivery order.")
     
#     @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            for picking in rec.picking_ids:
                picking.write({'attn': self.attn.id,
                                      'customer_po_no' :self.customer_po_no})
        for loop in rec.picking_ids:
            for move in loop.move_ids_without_package:
                move.customer_part_no = move.product_id.name
        return res
    
#     @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['attn'] = self.attn.id
        invoice_vals['customer_po_no'] = self.customer_po_no
        return invoice_vals
    
class SaleOrderLine(models.Model):   
    _inherit = "sale.order.line"
    
    customer_part_no = fields.Text(string='Customer Part No')
    need_date = fields.Date(string="Need Date")
    line_no = fields.Integer(string='Position' ,default=False)
    requested_date_line = fields.Date(string="Requested Date")
    order_ref = fields.Char('Order Reference',related='order_id.name')   
    customer_id = fields.Many2one('res.partner',related='order_id.partner_id')
    sales_person_id = fields.Many2one('res.users',related='order_id.user_id')
    promise_date = fields.Datetime('Promised Date',related='order_id.commitment_date')


#     @api.depends('sequence', 'order_id')
#     def _compute_get_number(self):
#         for recs in self:
#             for order in recs.mapped('order_id'):
#                 line_no_val = 1
#                 for line in order.order_line:
#                     line.line_no = line_no_val
#                     line_no_val += 1
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id.name:
            self.update({'customer_part_no':self.product_id.name,
                         'name':self.product_id.name})
      
            
        
