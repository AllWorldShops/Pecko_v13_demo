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
    

    @api.onchange('product_id')
    def onchange_purchase_line_product(self):
        if self.product_id:
            self.manufacturer_id = self.product_id.manufacturer_id
            
    @api.model
    def create(self, vals):
        product_id = self.env['product.product'].search([('id','=',vals['product_id'])])
        vals['manufacturer_id'] = product_id.product_tmpl_id.manufacturer_id.id
        return super(PurchaseOrderLine, self).create(vals)