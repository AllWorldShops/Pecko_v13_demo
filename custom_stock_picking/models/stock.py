# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from statistics import mode
from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.misc import split_every

from odoo.tools.float_utils import float_compare, float_is_zero
from odoo.tools import format_datetime, format_date, format_list, groupby, SQL

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

    def _sanity_check(self, separate_pickings=True):
        
        """ Sanity check for `button_validate()`
            :param separate_pickings: Indicates if pickings should be checked independently for lot/serial numbers or not.
        """
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        pickings_without_moves = self.filtered(lambda p: not p.move_ids and not p.move_line_ids)
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        no_quantities_done_ids = set()
        pickings_without_quantities = self.env['stock.picking']
        for picking in self:
            has_pick = any(move.picked and move.state not in ('done', 'cancel') for move in picking.move_ids)
            if all(float_is_zero(move.quantity, precision_digits=precision_digits) for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel') and (not has_pick or m.picked))):
                pickings_without_quantities |= picking

        pickings_using_lots = self.filtered(lambda p: p.picking_type_id.use_create_lots or p.picking_type_id.use_existing_lots)
        if pickings_using_lots:
            lines_to_check = pickings_using_lots._get_lot_move_lines_for_sanity_check(no_quantities_done_ids, separate_pickings)
            for line in lines_to_check:
                if not line.lot_name and not line.lot_id:
                    pickings_without_lots |= line.picking_id
                    products_without_lots |= line.product_id

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_("You can’t validate an empty transfer. Please add some products to move before proceeding."))
            # if pickings_without_quantities:
            #     raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                raise UserError(_('You need to supply a Lot/Serial number for products %s.', ', '.join(products_without_lots.mapped('display_name'))))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.', ', '.join(pickings_without_moves.mapped('name')))
            if pickings_without_lots:
                message += _(
                    '\n\nTransfers %(transfer_list)s: You need to supply a Lot/Serial number for products %(product_list)s.',
                    transfer_list=format_list(self.env, pickings_without_lots.mapped('name')),
                    product_list=format_list(self.env, products_without_lots.mapped('display_name')),
                )
            if message:
                raise UserError(message.lstrip())


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
    manufacturer_name = fields.Char(string='Manufacturer',related="product_id.product_tmpl_id.manufacturer_id.name", store=True, readonly=True)
    # related = 'product_id.manufacturer_id.name'

    @api.onchange('product_id')
    def _onchange_product_id_set_manufacturer(self):
        for move in self:
            if move.product_id and move.product_id.product_tmpl_id.manufacturer_id:
                move.manufacturer_name = move.product_id.product_tmpl_id.manufacturer_id.name
            else:
                move.manufacturer_name = ""

    @api.model
    def create(self, vals):
        if vals.get("product_id"):
            product = self.env["product.product"].browse(vals["product_id"])
            vals["manufacturer_name"] = product.product_tmpl_id.manufacturer_id.name or ""
        return super().create(vals)

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
                if rte.company_id == self.env.company:
                    return rte.ids
        return []
