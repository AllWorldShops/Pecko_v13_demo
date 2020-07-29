# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    attn = fields.Many2one('res.partner',string="ATTN")
    carrier = fields.Char(string='Carrier')
    customer_po_no = fields.Char(string="Customer PO No") 
    
    @api.model
    def create(self, vals):
        if vals.get('origin'):
            sale_id = self.env['sale.order'].search([('name','=',vals['origin'])])
            vals['customer_po_no'] = sale_id.customer_po_no
        return super(StockPicking, self).create(vals) 
    
class StockMove(models.Model):
    _inherit = 'stock.move'
    
    additional_notes = fields.Char(string='Additional Notes')
    customer_part_no = fields.Text(string='Part Number')
    
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    customer_part_no = fields.Text(string='Part Number',compute="_compute_product_name",store=True)
    
    
    @api.depends('product_id')
    def _compute_product_name(self):
        for pro in self:
            if pro.product_id:
                pro.customer_part_no = pro.product_id.name
            else:
                pro.customer_part_no = ''
