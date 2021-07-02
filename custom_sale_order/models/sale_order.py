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
    promise_date = fields.Datetime('Delivery Date',related='order_id.commitment_date')
    promised_date = fields.Date(string="Promised Date")
    customer_po_no = fields.Char('Customer Po No',related='order_id.customer_po_no')   
    internal_ref_no = fields.Char('Internal Ref No',related='product_id.default_code') 
    back_order_qty = fields.Integer(string='Back Order Qty', compute='_compute_back_order_qty', store=True)
  

#     @api.depends('sequence', 'order_id')
#     def _compute_get_number(self):
#         for recs in self:
#             for order in recs.mapped('order_id'):
#                 line_no_val = 1
#                 for line in order.order_line:
#                     line.line_no = line_no_val
#                     line_no_val += 1
    
    @api.depends('product_uom_qty','qty_delivered')
    def _compute_back_order_qty(self):
        for pro in self:
            if pro.qty_delivered:
                pro.back_order_qty = pro.product_uom_qty - pro.qty_delivered
            else:
                pro.back_order_qty = 0
                
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id.name:
            self.update({'customer_part_no':self.product_id.name,
                         'name':self.product_id.name})
            
            
class AccountGeneralLedgerReport(models.AbstractModel):
    _inherit = "account.general.ledger"
    
    @api.model
    def _get_account_total_line(self, options, account, amount_currency, debit, credit, balance):
        return {
            'id': 'total_%s' % account.id,
            'class': 'o_account_reports_domain_total',
            'parent_id': 'account_%s' % account.id,
            'name': _('Total'),
            'columns': [
                {'name': '', 'class': 'number'},
                {'name': self.format_value(debit), 'class': 'number'},
                {'name': self.format_value(credit), 'class': 'number'},
                {'name': self.format_value(balance), 'class': 'number'},
            ],
            'colspan': 4,
        }
      
            
        
