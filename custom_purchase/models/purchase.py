# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    old_po_no = fields.Char(string='Old PO Number')

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer')
    notes = fields.Char(string='Notes')
    order_ref = fields.Char('Order Reference',related='order_id.name')   
    vendor_id = fields.Many2one('res.partner',related='order_id.partner_id')
    schedule_date = fields.Datetime(related='order_id.date_planned')
    promise_date = fields.Datetime(string="Promised Date")
    order_date = fields.Datetime(related='order_id.date_order')
    back_order_qty = fields.Integer(string='Back Order Qty', compute='_compute_back_order_qty', store=True)
    line_no = fields.Integer(string='Position', default=False)
    old_po_no = fields.Char(string="Old PO Number", related="order_id.old_po_no")
    
    @api.depends('product_qty','qty_received')
    def _compute_back_order_qty(self):
        for pro in self:
            if pro.qty_received:
                pro.back_order_qty = pro.product_qty - pro.qty_received
            else:
                pro.back_order_qty = 0

    @api.onchange('product_id')
    def onchange_purchase_line_product(self):
        if self.product_id:
            self.manufacturer_id = self.product_id.manufacturer_id
            
    @api.model
    def create(self, vals):
        if vals['product_id']:
            product_id = self.env['product.product'].search([('id','=',vals['product_id'])])
            vals['manufacturer_id'] = product_id.product_tmpl_id.manufacturer_id.id
        return super(PurchaseOrderLine, self).create(vals)
    
class PurchaseOrdLine(models.Model):
    _inherit = 'purchase.order.line'
    
    item_text = fields.Char("Item Text", related='product_id.item_text')
