# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from statistics import mode
from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.misc import split_every


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    attn = fields.Many2one('res.partner',string="ATTN")
    carrier = fields.Char(string='Carrier')
    customer_po_no = fields.Char(string="Customer PO No")
    picking_type_code = fields.Selection([('incoming', 'Receipt'),('outgoing', 'Delivery'),('internal','Internal Transfer'),('mrp_operation','Manufacturing')], related='picking_type_id.code',string="Picking Type Code") 
    packing_slip = fields.Char(string="Packing Slip / DO No", copy=False)
    
    @api.constrains('packing_slip')
    def _check_packing_slip(self):
        for rec in self:
            if rec.packing_slip:
                existing_records = self.search([('packing_slip', '=', rec.packing_slip)])
                print("\n\n\n===",len(existing_records))
                if len(existing_records) > 1:
                    raise ValidationError(_('There is already a packing slip/Do Number for "%s". Please enter a new number.' %rec.packing_slip))

    @api.model
    def create(self, vals):
        if vals.get('origin'):
            sale_id = self.env['sale.order'].search([('name','=',vals['origin'])])
            vals['customer_po_no'] = sale_id.customer_po_no
        return super(StockPicking, self).create(vals)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_unreserve(self):
        assigned_moves = self.sudo().search([('location_id', '=', 8), ('state', 'in', ['assigned', 'partially_available'])])
        _logger.info("---------Assigned stock moves -------: %s", len(assigned_moves))
        for rec in assigned_moves:
            try:
                rec.sudo()._do_unreserve()
            except Exception as e:
                _logger.info("-----Exception occurred stock moves--------- : %s", str(e))

    additional_notes = fields.Char(string='Additional Notes')
    customer_part_no = fields.Text(string='Part Number')
    position_no = fields.Integer(string="Position", compute="_compute_position_no")

    def _compute_position_no(self):
        for move in self:
            if move.sale_line_id:
                move.position_no = move.sale_line_id.line_no
            elif move.purchase_line_id:
                move.position_no = move.purchase_line_id.line_no
            elif move.bom_line_id:
                move.position_no = move.bom_line_id.x_studio_field_c9hp1
            else:
                move.position_no = 0
    
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    part_no = fields.Char('Customer / Manufacturer Part no', related="product_id.name")
    position_no = fields.Integer(string="Position", compute="_compute_position_no")
    product_uom_qty = fields.Float(string="Demand Qty", related="move_id.product_uom_qty")

    def _compute_position_no(self):
        for line in self:
            if line.move_id.sale_line_id:
                line.position_no = line.move_id.sale_line_id.line_no
            elif line.move_id.purchase_line_id:
                line.position_no = line.move_id.purchase_line_id.line_no
            elif line.move_id.bom_line_id:
                line.position_no = line.move_id.bom_line_id.x_studio_field_c9hp1
            else:
                line.position_no = 0

class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'
    
    route_ids = fields.Many2many(default=lambda self:self._get_default_buy())
    
    @api.model
    def _get_default_buy(self):
        buy_route = self.env.ref('purchase_stock.route_warehouse0_buy', raise_if_not_found=False)
        if buy_route:
            route = self.env['stock.route'].sudo().search(['|',('id', '=', buy_route.id),('name', 'ilike', 'PEI - Buy from Vendor')])
            for rte in route:
                # print(rte.name,"////_--------------;;;;;;;", rte)
                if rte.company_id == self.env.company:
                    return rte.ids
        return []
