# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from statistics import mode
from odoo import models, fields, api, _
from datetime import date

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    attn = fields.Many2one('res.partner',string="ATTN")
    carrier = fields.Char(string='Carrier')
    customer_po_no = fields.Char(string="Customer PO No") 
    picking_type_code = fields.Selection([('incoming', 'Receipt'),('outgoing', 'Delivery'),('internal','Internal Transfer'),('mrp_operation','Manufacturing')], related='picking_type_id.code',string="Picking Type Code") 
    packing_slip = fields.Char(string="Packing Slip / DO No")
    
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
    
    part_no = fields.Char('Customer / Manufacturer Part no', related="product_id.name")


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    route_ids = fields.Many2many(default=lambda self:self._get_default_buy())
    
    @api.model
    def _get_default_buy(self):
        buy_route = self.env.ref('purchase_stock.route_warehouse0_buy', raise_if_not_found=False)
        if buy_route:
            route = self.env['stock.location.route'].sudo().search(['|',('id', '=', buy_route.id),('name', 'ilike', 'PEI - Buy from Vendor')])
            for rte in route:
                print(rte.name,"////_--------------;;;;;;;", rte)
                if rte.company_id == self.env.company:
                    return rte.ids
        return []