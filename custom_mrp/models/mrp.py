from email.policy import default
from odoo import models, fields, api, _
from odoo.tools import float_round
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, format_date, float_is_zero

import datetime
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _action_cancel_orders(self):
        mrp = self.sudo().search([('order_seq', 'ilike', 'C-'), ('state', '!=', 'cancel')], limit=1000)
        for rec in mrp:
            rec.with_delay().action_cancel()

    consumed_move_raw_ids = fields.One2many(related='move_raw_ids', string="Consumed Products")
    finished_line_ids = fields.One2many(related='finished_move_line_ids', string="Consumed Products")
    manufacturer_id = fields.Many2one('product.manufacturer', string='Manufacturer Name')
    customer_part_no = fields.Char(string='Part Number')
    description = fields.Char(string='Description')
    customer_part_number = fields.Char(string='Customer Part Number', related='product_id.product_tmpl_id.customer_part_number', store=True, readonly=True)
    transfer_done_flag = fields.Boolean(string='Transfer Done Flag', compute='_compute_boolean_txt')
    project = fields.Char(string='Project', related='product_tmpl_id.project', store=True)
    start_date = fields.Date('Start Date P2')
    start_date_one = fields.Date('Start Date P1')
    order_seq = fields.Char(string='Order Sequence')
    production_cell = fields.Char(string='Production Cell', related='product_tmpl_id.production_cell', store=True)
    # reserved = fields.Boolean("Reserved Compute")
    reserved_check = fields.Boolean("Reserved", compute="_compute_reserved")
    customer_po_no = fields.Char(string="Customer PO No")
    store_start_date = fields.Date("Store Start Date")
    confirm_cancel = fields.Boolean(compute='_compute_confirm_cancel')

    def _compute_boolean_txt(self):
        res = self.env['stock.picking'].search(
            [('id', 'in', self.picking_ids.ids), ('picking_type_id.name', '!=', 'Store Finished Product')])
        count = 0
        done_count = 0
        for rec in res:
            count += 1
            if rec.state == 'done':
                done_count += 1
        if count == done_count:
            self.transfer_done_flag = True
        else:
            self.transfer_done_flag = False

        wo_flag = self.env['ir.config_parameter'].sudo().get_param(
            'custom_mrp.workorder_flag')

        if wo_flag:
            # The reserved_availability field has been deprecated with quantity in Odoo 18

            reserved_qty = self.move_raw_ids.filtered(
                lambda l: l.quantity != 0 and l.product_uom_qty != 0)
            if reserved_qty and self.state not in ['draft', 'done']:
                self.transfer_done_flag = True

    def _compute_reserved(self):
        # reserved_qty = []
        wo_flag = self.env['ir.config_parameter'].sudo().get_param(
            'custom_mrp.workorder_flag')
        for rec in self:
            rec.reserved_check = False
            if wo_flag:
                # The reserved_availability field has been deprecated with quantity in Odoo 18

                reserved_qty = self.move_raw_ids.filtered(
                    lambda l: l.quantity == 0 and l.product_uom_qty != 0)
                if reserved_qty and rec.state not in ['draft', 'done']:
                    rec.reserved_check = True

    @api.onchange('product_id')
    def onchange_responsible(self):
        if self.product_id:
            self.user_id = self.product_id.responsible_id.id

    @api.onchange('product_id')
    def onchange_mrp_product(self):
        for mrp_product in self:
            if mrp_product.product_id:
                mrp_product.manufacturer_id = mrp_product.product_id.product_tmpl_id.manufacturer_id
                mrp_product.customer_part_no = mrp_product.product_id.name
                mrp_product.description = mrp_product.product_id.product_tmpl_id.x_studio_field_mHzKJ

    @api.model
    def create(self, vals):
        product_id = self.env['product.product'].search([('id', '=', vals['product_id'])])
        vals['manufacturer_id'] = product_id.product_tmpl_id.manufacturer_id.id
        vals['customer_part_no'] = product_id.name
        vals['description'] = product_id.product_tmpl_id.x_studio_field_mHzKJ
        return super(MrpProduction, self).create(vals)

    def _get_move_raw_values(self, product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        res = super(MrpProduction, self)._get_move_raw_values(product_id, product_uom_qty, product_uom, operation_id,
                                                              bom_line)
        res['name'] = bom_line.product_id.product_tmpl_id.x_studio_field_mHzKJ if bom_line.product_id.product_tmpl_id.x_studio_field_mHzKJ else self.name
        return res


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    customer_part_number = fields.Char(string='Part Number',related='product_tmpl_id.x_studio_field_qr3ai',store=True)
    mpn_customer_supplier_partno = fields.Char(string="MPN/Customer/Supplier Part No", related="product_tmpl_id.x_studio_field_qr3ai",store=False)


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    manufacturer_id = fields.Many2one('product.manufacturer', string='Manufacturer')
    customer_part_no = fields.Text(string='Part Number', compute="_compute_product_name", store=True)
    item_text = fields.Char("Item Text", related='product_id.item_text')

    @api.depends('product_id')
    def _compute_product_name(self):
        for pro in self:
            if pro.product_id:
                pro.customer_part_no = pro.product_id.name
            else:
                pro.customer_part_no = ''

    @api.onchange('product_id')
    def onchange_mrp_product(self):
        if self.product_id:
            self.manufacturer_id = self.product_id.manufacturer_id
            self.x_studio_field_gVfQK = self.product_id.product_tmpl_id.x_studio_field_mHzKJ


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    position_no = fields.Integer(string="Position", help="Auto line number")

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    position_no = fields.Integer(string="Position", help="Auto line number")

    @api.model
    def update_existing_position_no(self):
        workorders = self.search([], order='id')  # Or order by any preferred field
        for idx, workorder in enumerate(workorders, start=1):
            workorder.position_no = idx


class StockMove(models.Model):
    _inherit = 'stock.move'

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

    storage_location_id = fields.Char(string='Storage Location', company_dependent=True, store=True)
    to_consume_qty = fields.Float(string="To Consume Quantity", compute='_get_consumed_data')
    manufacturer_id = fields.Many2one('product.manufacturer', string='Manufacturer Name')
    customer_part_no = fields.Text(string='Part Number', compute="_compute_product_name", store=True)
    item_text = fields.Char("Item Text", related='product_id.item_text')
    position_no = fields.Integer(string="Position", compute="_compute_position_no")

    @api.depends('product_id')
    def _compute_product_name(self):
        for pro in self:
            if pro.product_id:
                pro.customer_part_no = pro.product_id.name
            else:
                pro.customer_part_no = ' '

    @api.model
    def create(self, vals):
        product_id = self.env['product.product'].search([('id', '=', vals['product_id'])])
        vals['storage_location_id'] = product_id.product_tmpl_id.storage_location_id
        vals['manufacturer_id'] = product_id.product_tmpl_id.manufacturer_id.id
        vals['description_picking'] = product_id.product_tmpl_id.x_studio_field_mHzKJ

        if product_id.product_tmpl_id.x_studio_field_mHzKJ:
            vals['name'] = product_id.product_tmpl_id.x_studio_field_mHzKJ
        else:
            if vals.get('sale_line_id'):
                sale_line_id = self.env['sale.order.line'].search([('id', '=', vals.get('sale_line_id'))])
                vals['name'] = sale_line_id.name
            if vals.get('purchase_line_id'):
                purchase_line_id = self.env['purchase.order.line'].search([('id', '=', vals.get('purchase_line_id'))])
                vals['name'] = purchase_line_id.name
        return super(StockMove, self).create(vals)

    @api.depends('product_uom_qty')
    def _get_consumed_data(self):
        for rec in self:
            rec.to_consume_qty = rec.product_uom_qty - rec.quantity


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    qty_to_produce = fields.Float(compute='_to_produce_qty', string="Quantity To Produce")

    @api.depends('move_id')
    def _to_produce_qty(self):
        for rec in self:
            rec.qty_to_produce = rec.move_id.product_uom_qty - rec.qty_done


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrderInherit, self).action_confirm()
        mrp = self.env['mrp.production'].search([('origin', '=', self.name)])
        if mrp:
            for rec in mrp:
                rec.user_id = rec.product_id.responsible_id.id or False
                rec.customer_po_no = self.customer_po_no

        return res


class ReportBomStructureInherit(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    @api.model
    def _compute_current_production_capacity(self, bom_data):
        # Get the maximum amount producible product of the selected bom given each component's stock levels.
        components_qty_to_produce = defaultdict(lambda: 0)
        components_qty_available = {}
        for comp in bom_data.get('components', []):
            if not comp['product'].is_storable or float_is_zero(comp['base_bom_line_qty'],
                                                                precision_rounding=comp['uom'].rounding):
                continue
            components_qty_to_produce[comp['product_id']] += comp['base_bom_line_qty']
            components_qty_available[comp['product_id']] = comp['free_to_manufacture_qty']
        producibles = [float_round(components_qty_available[p_id] / qty, precision_digits=0, rounding_method='DOWN') for
                       p_id, qty in components_qty_to_produce.items()]
        return min(producibles) * bom_data['bom']['product_qty'] if producibles else 0

    @api.model
    def _get_bom_data(self, bom, warehouse, product=False, line_qty=False, bom_line=False, level=0, parent_bom=False,
                      parent_product=False, index=0, product_info=False, ignore_stock=False,
                      simulated_leaves_per_workcenter=False):
        """ Gets recursively the BoM and all its subassemblies and computes availibility estimations for each component and their disponibility in stock.
            Accepts specific keys in context that will affect the data computed :
            - 'minimized': Will cut all data not required to compute availability estimations.
            - 'from_date': Gives a single value for 'today' across the functions, as well as using this date in products quantity computes.
        """
        is_minimized = self.env.context.get('minimized', False)
        if not product:
            product = bom.product_id or bom.product_tmpl_id.product_variant_id
        if line_qty is False:
            line_qty = bom.product_qty
        if not product_info:
            product_info = {}
        if simulated_leaves_per_workcenter is False:
            simulated_leaves_per_workcenter = defaultdict(list)

        company = bom.company_id or self.env.company
        current_quantity = line_qty
        if bom_line:
            current_quantity = bom_line.product_uom_id._compute_quantity(line_qty, bom.product_uom_id) or 0

        prod_cost = 0
        has_attachments = []

        if not is_minimized:
            if product:
                prod_cost = product.uom_id._compute_price(product.with_company(company).standard_price,
                                                          bom.product_uom_id) * current_quantity
                has_attachments = self.env['product.document'].search_count(
                    ['&', '&', ('attached_on_mrp', '=', 'bom'), ('active', '=', 't'), '|', '&',
                     ('res_model', '=', 'product.product'),
                     ('res_id', '=', product.id), '&', ('res_model', '=', 'product.template'),
                     ('res_id', '=', product.product_tmpl_id.id)], limit=1) > 0
            else:
                # Use the product template instead of the variant
                prod_cost = bom.product_tmpl_id.uom_id._compute_price(
                    bom.product_tmpl_id.with_company(company).standard_price, bom.product_uom_id) * current_quantity
                has_attachments = self.env['product.document'].search_count(
                    ['&', '&', ('attached_on_mrp', '=', 'bom'), ('active', '=', 't'),
                     '&', ('res_model', '=', 'product.template'), ('res_id', '=', bom.product_tmpl_id.id)], limit=1) > 0

        key = product.id
        bom_key = bom.id
        qty_product_uom = bom.product_uom_id._compute_quantity(current_quantity,
                                                               product.uom_id or bom.product_tmpl_id.uom_id)
        self._update_product_info(product, bom_key, product_info, warehouse, qty_product_uom, bom=bom,
                                  parent_bom=parent_bom, parent_product=parent_product)
        route_info = product_info[key].get(bom_key, {})
        quantities_info = {}
        if not ignore_stock:
            # Useless to compute quantities_info if it's not going to be used later on
            quantities_info = self._get_quantities_info(product, bom.product_uom_id, product_info, parent_bom,
                                                        parent_product)
        workorder_list = []
        for line in bom.operation_ids:
            workorder_list.append({'name': line.name,
                                   'workcenter': line.workcenter_id.name,
                                   'note': line.note,
                                   })
        bom_report_line = {
            'index': index,
            'bom': bom,
            'bom_id': bom and bom.id or False,
            'bom_code': bom and bom.code or False,
            'product_discription': bom.product_tmpl_id.x_studio_field_mHzKJ,
            'product_part_no': bom.product_tmpl_id.x_studio_field_qr3ai,
            'type': 'bom',
            'quantity': current_quantity,
            'quantity_available': quantities_info.get('free_qty', 0),
            'quantity_on_hand': quantities_info.get('on_hand_qty', 0),
            'base_bom_line_qty': bom_line.product_qty if bom_line else False,
            # bom_line isn't defined only for the top-level product
            'name': product.display_name or bom.product_tmpl_id.display_name,
            'uom': bom.product_uom_id if bom else product.uom_id,
            'uom_name': bom.product_uom_id.name if bom else product.uom_id.name,
            'route_type': route_info.get('route_type', ''),
            'route_name': route_info.get('route_name', ''),
            'route_detail': route_info.get('route_detail', ''),
            'lead_time': route_info.get('lead_time', False),
            'currency': company.currency_id,
            'currency_id': company.currency_id.id,
            'product': product,
            'product_id': product.id,
            'link_id': (
                           product.id if product.product_variant_count > 1 else product.product_tmpl_id.id) or bom.product_tmpl_id.id,
            'link_model': 'product.product' if product.product_variant_count > 1 else 'product.template',
            'code': bom and bom.display_name or '',
            'prod_cost': prod_cost,
            'bom_cost': 0,
            'level': level or 0,
            'has_attachments': has_attachments,
            'phantom_bom': bom.type == 'phantom',
            'parent_id': parent_bom and parent_bom.id or False,
            'workorder_ids': workorder_list
        }

        components = []
        no_bom_lines = self.env['mrp.bom.line']
        line_quantities = {}
        for line in bom.bom_line_ids:
            if product and line._skip_bom_line(product):
                continue
            line_quantity = (current_quantity / (bom.product_qty or 1.0)) * line.product_qty
            line_quantities[line.id] = line_quantity
            if not line.child_bom_id:
                no_bom_lines |= line
                # Update product_info for all the components before computing closest forecasted.
                qty_product_uom = line.product_uom_id._compute_quantity(line_quantity, line.product_id.uom_id)
                self._update_product_info(line.product_id, bom.id, product_info, warehouse, qty_product_uom, bom=False,
                                          parent_bom=bom, parent_product=product)
        components_closest_forecasted = self._get_components_closest_forecasted(no_bom_lines, line_quantities, bom,
                                                                                product_info, product, ignore_stock)
        for component_index, line in enumerate(bom.bom_line_ids):
            new_index = f"{index}{component_index}"
            if product and line._skip_bom_line(product):
                continue
            line_quantity = line_quantities.get(line.id, 0.0)
            if line.child_bom_id:
                component = self._get_bom_data(line.child_bom_id, warehouse, line.product_id, line_quantity,
                                               bom_line=line, level=level + 1, parent_bom=bom,
                                               parent_product=product, index=new_index, product_info=product_info,
                                               ignore_stock=ignore_stock,
                                               simulated_leaves_per_workcenter=simulated_leaves_per_workcenter)
            else:
                component = self.with_context(
                    components_closest_forecasted=components_closest_forecasted,
                )._get_component_data(bom, product, warehouse, line, line_quantity, level + 1, new_index, product_info,
                                      ignore_stock)
            for component_bom in components:
                if component['product_id'] == component_bom['product_id'] and component['uom'].id == component_bom[
                    'uom'].id:
                    self._merge_components(component_bom, component)
                    break
            else:
                components.append(component)
            bom_report_line['bom_cost'] += component['bom_cost']
        bom_report_line['components'] = components
        # bom_report_line['producible_qty'] = self._compute_current_production_capacity(bom_report_line)

        availabilities = self._get_availabilities(product, current_quantity, product_info, bom_key, quantities_info,
                                                  level, ignore_stock, components, report_line=bom_report_line)
        # in case of subcontracting, lead_time will be calculated with components availability delay
        bom_report_line['lead_time'] = route_info.get('lead_time', False)
        bom_report_line['manufacture_delay'] = route_info.get('manufacture_delay', False)
        bom_report_line.update(availabilities)

        if not is_minimized:

            operations = self._get_operation_line(product, bom, float_round(current_quantity, precision_rounding=1,
                                                                            rounding_method='UP'), level + 1, index,
                                                  bom_report_line, simulated_leaves_per_workcenter)
            bom_report_line['operations'] = operations
            bom_report_line['operations_cost'] = sum(op['bom_cost'] for op in operations)
            bom_report_line['operations_time'] = sum(op['quantity'] for op in operations)
            bom_report_line['operations_delay'] = max((op['availability_delay'] for op in operations), default=0)
            if 'simulated' in bom_report_line:
                bom_report_line['availability_state'] = 'estimated'
                max_component_delay = bom_report_line['max_component_delay']
                bom_report_line['availability_delay'] = max_component_delay + max(bom.produce_delay,
                                                                                  bom_report_line['operations_delay'])
                bom_report_line['availability_display'] = self._format_date_display(
                    bom_report_line['availability_state'], bom_report_line['availability_delay'])
            bom_report_line['bom_cost'] += bom_report_line['operations_cost']

            byproducts, byproduct_cost_portion = self._get_byproducts_lines(product, bom, current_quantity, level + 1,
                                                                            bom_report_line['bom_cost'], index)
            bom_report_line['byproducts'] = byproducts
            bom_report_line['cost_share'] = float_round(1 - byproduct_cost_portion, precision_rounding=0.0001)
            bom_report_line['byproducts_cost'] = sum(byproduct['bom_cost'] for byproduct in byproducts)
            bom_report_line['byproducts_total'] = sum(byproduct['quantity'] for byproduct in byproducts)
            bom_report_line['bom_cost'] *= bom_report_line['cost_share']

        if level == 0:
            # Gives a unique key for the first line that indicates if product is ready for production right now.
            bom_report_line['components_available'] = all([c['stock_avail_state'] == 'available' for c in components])
        return bom_report_line

    @api.model
    def _get_component_data(self, parent_bom, parent_product, warehouse, bom_line, line_quantity, level, index,
                            product_info, ignore_stock=False):
        company = parent_bom.company_id or self.env.company
        price = bom_line.product_id.uom_id._compute_price(bom_line.product_id.with_company(company).standard_price,
                                                          bom_line.product_uom_id) * line_quantity
        rounded_price = company.currency_id.round(price)

        key = bom_line.product_id.id
        bom_key = parent_bom.id
        route_info = product_info[key].get(bom_key, {})

        quantities_info = {}
        if not ignore_stock:
            # Useless to compute quantities_info if it's not going to be used later on
            quantities_info = self._get_quantities_info(bom_line.product_id, bom_line.product_uom_id, product_info,
                                                        parent_bom, parent_product)
        availabilities = self._get_availabilities(bom_line.product_id, line_quantity, product_info, bom_key,
                                                  quantities_info, level, ignore_stock, bom_line=bom_line)

        has_attachments = False
        if not self.env.context.get('minimized', False):
            has_attachments = self.env['product.document'].search_count(
                ['&', ('attached_on_mrp', '=', 'bom'), '|', '&', ('res_model', '=', 'product.product'),
                 ('res_id', '=', bom_line.product_id.id),
                 '&', ('res_model', '=', 'product.template'),
                 ('res_id', '=', bom_line.product_id.product_tmpl_id.id)]) > 0

        return {
            'type': 'component',
            'index': index,
            'bom_id': False,
            'product_name': bom_line.product_id.x_studio_field_qr3ai,
            'product': bom_line.product_id,
            'product_id': bom_line.product_id.id,
            'position_no': bom_line.x_studio_field_c9hp1,
            'part_no': bom_line.customer_part_no,
            'description': bom_line.x_studio_field_gVfQK,
            'manufacturer': bom_line.manufacturer_id.name,
            'link_id': bom_line.product_id.id if bom_line.product_id.product_variant_count > 1 else bom_line.product_id.product_tmpl_id.id,
            'link_model': 'product.product' if bom_line.product_id.product_variant_count > 1 else 'product.template',
            'name': bom_line.product_id.display_name,
            'code': '',
            'currency': company.currency_id,
            'currency_id': company.currency_id.id,
            'quantity': line_quantity,
            'quantity_available': quantities_info.get('free_qty', 0),
            'quantity_on_hand': quantities_info.get('on_hand_qty', 0),
            'base_bom_line_qty': bom_line.product_qty,
            'uom': bom_line.product_uom_id,
            'uom_name': bom_line.product_uom_id.name,
            'prod_cost': rounded_price,
            'prod_cost_unit': bom_line.product_id.standard_price,
            'bom_cost': rounded_price,
            'route_type': route_info.get('route_type', ''),
            'route_name': route_info.get('route_name', ''),
            'route_detail': route_info.get('route_detail', ''),
            'lead_time': route_info.get('lead_time', False),
            'stock_avail_state': availabilities['stock_avail_state'],
            'resupply_avail_delay': availabilities['resupply_avail_delay'],
            'availability_display': availabilities['availability_display'],
            'availability_state': availabilities['availability_state'],
            'availability_delay': availabilities['availability_delay'],
            'parent_id': parent_bom.id,
            'level': level or 0,
            'has_attachments': has_attachments,
        }

    @api.model
    def _get_bom_array_lines(self, data, level, unfolded_ids, unfolded, parent_unfolded=True):
        bom_lines = data['components']
        lines = []
        for bom_line in bom_lines:
            line_unfolded = ('bom_' + str(bom_line['index'])) in unfolded_ids
            line_visible = level == 1 or unfolded or parent_unfolded
            lines.append({
                'bom_id': bom_line['bom_id'],
                'name': bom_line['name'],
                'type': bom_line['type'],
                'product_name': bom_line['product_name'] if 'product_name' in bom_line else '',
                'description': bom_line['description'] if 'description' in bom_line else '',
                'position_no': bom_line['position_no'] if 'position_no' in bom_line else '',
                'part_no': bom_line['part_no'] if 'part_no' in bom_line else '',
                'manufacturer': bom_line['manufacturer'] if 'manufacturer' in bom_line else '',
                'quantity': bom_line['quantity'],
                'quantity_available': bom_line['quantity_available'],
                'quantity_on_hand': bom_line['quantity_on_hand'],
                'producible_qty': bom_line.get('producible_qty', False),
                'uom': bom_line['uom_name'],
                'prod_cost': bom_line['prod_cost'],
                'prod_cost_unit': bom_line['prod_cost_unit'] if 'prod_cost_unit' in bom_line else '',
                'bom_cost': bom_line['bom_cost'],
                'route_name': bom_line['route_name'],
                'route_detail': bom_line['route_detail'],
                'lead_time': bom_line['lead_time'],
                'level': bom_line['level'],
                'code': bom_line['code'],
                'availability_state': bom_line['availability_state'],
                'availability_display': bom_line['availability_display'],
                'visible': line_visible,
            })
            if bom_line.get('components'):
                lines += self._get_bom_array_lines(bom_line, level + 1, unfolded_ids, unfolded,
                                                   line_visible and line_unfolded)

        if data['operations']:
            lines.append({
                'name': _('Operations'),
                'type': 'operation',
                'quantity': data['operations_time'],
                'uom': _('minutes'),
                'bom_cost': data['operations_cost'],
                'level': level,
                'visible': parent_unfolded,
            })
            operations_unfolded = unfolded or (parent_unfolded and ('operations_' + str(data['index'])) in unfolded_ids)
            for operation in data['operations']:
                lines.append({
                    'name': operation['name'],
                    'type': 'operation',
                    'quantity': operation['quantity'],
                    'uom': _('minutes'),
                    'bom_cost': operation['bom_cost'],
                    'level': level + 1,
                    'availability_state': operation['availability_state'],
                    'availability_delay': operation['availability_delay'],
                    'availability_display': operation['availability_display'],
                    'visible': operations_unfolded,
                })
        if data['byproducts']:
            lines.append({
                'name': _('Byproducts'),
                'type': 'byproduct',
                'uom': False,
                'quantity': data['byproducts_total'],
                'bom_cost': data['byproducts_cost'],
                'level': level,
                'visible': parent_unfolded,
            })
            byproducts_unfolded = unfolded or (parent_unfolded and ('byproducts_' + str(data['index'])) in unfolded_ids)
            for byproduct in data['byproducts']:
                lines.append({
                    'name': byproduct['name'],
                    'type': 'byproduct',
                    'quantity': byproduct['quantity'],
                    'uom': byproduct['uom_name'],
                    'prod_cost': byproduct['prod_cost'],
                    'bom_cost': byproduct['bom_cost'],
                    'level': level + 1,
                    'visible': byproducts_unfolded,
                })
        return lines
