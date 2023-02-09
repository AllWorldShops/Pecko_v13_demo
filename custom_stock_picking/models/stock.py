# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from statistics import mode
from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import Warning, ValidationError, UserError
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


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def action_open_inventory_lines(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('stock.stock_inventory_line_tree2').id, 'tree')],
            'view_mode': 'tree',
            'name': _('Inventory Lines'),
            'res_model': 'stock.inventory.line',
        }
        context = {
            'default_is_editable': True,
            'default_inventory_id': self.id,
            'default_company_id': self.company_id.id,
        }
        # Define domains and context
        domain = [
            ('inventory_id', '=', self.id)
        ]
        if self.location_ids:
            context['default_location_id'] = self.location_ids[0].id
            if len(self.location_ids) == 1:
                if not self.location_ids[0].child_ids:
                    context['readonly_location_id'] = True

        if self.product_ids:
            if len(self.product_ids) == 1:
                context['default_product_id'] = self.product_ids[0].id

        action['context'] = context
        action['domain'] = domain
        return action

    location_ids = fields.Many2many(
        'stock.location', string='Locations',
        readonly=True, check_company=True,
        states={'draft': [('readonly', False)]},
        domain="[('company_id', '=', company_id)]")

class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    @api.model
    def _domain_location_id(self):
        if self.env.context.get('active_model') == 'stock.inventory':
            inventory = self.env['stock.inventory'].browse(self.env.context.get('active_id'))
            if inventory.exists() and inventory.location_ids:
                return "[('company_id', '=', company_id), ('id', 'child_of', %s)]" % inventory.location_ids.ids
        return "[('company_id', '=', company_id)]"

    def _check_no_duplicate_line(self):
        for line in self:
            domain = [
                ('id', '!=', line.id),
                ('product_id', '=', line.product_id.id),
                ('location_id', '=', line.location_id.id),
                ('partner_id', '=', line.partner_id.id),
                ('package_id', '=', line.package_id.id),
                ('prod_lot_id', '=', line.prod_lot_id.id),
                ('inventory_id', '=', line.inventory_id.id),
                ('state', '!=', 'done')]
            # if line.location_id.usage != 'internal':
            #     dmn = self.search(domain)
            #     _logger.info("-------Duplicate Lineitem : %s------" % dmn)
            #     dmn.unlink()
            rec = self.search(domain)
            _logger.info("-------Duplicate Lineitem : %s------" % rec.inventory_id)
            existings = self.search_count(domain)
            if existings:
                raise UserError(_("There is already one inventory adjustment line for this product,"
                                  " you should rather modify this one instead of creating a new one."))


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
                # print(rte.name,"////_--------------;;;;;;;", rte)
                if rte.company_id == self.env.company:
                    return rte.ids
        return []


class StockLocation(models.Model):
    _inherit = "stock.location"

    def _should_be_valued(self):
        """ This method returns a boolean reflecting whether the products stored in `self` should
        be considered when valuating the stock of a company.
        """
        self.ensure_one()
        if self.usage == 'internal' or (self.usage == 'transit' and self.company_id) or (self.usage == 'production' and self.company_id):
            return True
        return False


class ProcurementRule(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def _run_scheduler_tasks(self, use_new_cursor=False, company_id=False):
        # Minimum stock rules
        self.sudo()._procure_orderpoint_confirm(use_new_cursor=use_new_cursor, company_id=company_id)
        if use_new_cursor:
            self._cr.commit()
        # Search all confirmed stock_moves and try to assign them
        # domain = self._get_moves_to_assign_domain(company_id)
        # moves_to_assign = self.env['stock.move'].search(domain, limit=None,
        #     order='priority desc, date_expected asc')
        # for moves_chunk in split_every(100, moves_to_assign.ids):
        #     self.env['stock.move'].browse(moves_chunk).sudo()._action_assign()
        #     if use_new_cursor:
        #         self._cr.commit()
        _logger.info("doneeeeeeeeeeeeeeeeee")
        # Merge duplicated quants
        self.env['stock.quant']._quant_tasks()
        if use_new_cursor:
            self._cr.commit()
        _logger.info("tooooooooooooooo")