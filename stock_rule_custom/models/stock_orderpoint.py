# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID, _
from collections import defaultdict
from odoo.tools import float_compare, split_every
from datetime import datetime, time
import logging
_logger = logging.getLogger(__name__)

class StockOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    def _get_orderpoint_procurement_date(self):
        Move = self.env['stock.move'].with_context(active_test=False)
        _logger.info("-----------Product_Id-------%s " % self.product_id.id)
        domain_move_out_todo = [('product_id', '=', self.product_id.id), ('sale_line_id', '!=', None),('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))]
        # print([s.id for s in Move.search(domain_move_out_todo)], "domain_move_out_todo============")
        out_moves = Move.search(domain_move_out_todo)
        _logger.info("out_movesout_moves-------%s " % str(out_moves))
        deadline_date = False
        if out_moves:
            deadline_date = min(out_moves.mapped('date'), default=fields.Datetime.now())
        # sale = self.env['sale.order.line'].search([('')])
        _logger.info("-----------Order Point-------%s " % self.id)
        _logger.info("Deadline date time: %s------------Lead date time : %s" % (deadline_date, self.lead_days_date))
        # return datetime.combine(self.lead_days_date, time.min)
        lead_date = date_now = fields.Datetime.now()
        if deadline_date:
            lead_date = deadline_date
            if deadline_date <= date_now:
                lead_date = date_now
        else:
            lead_date = datetime.combine(self.lead_days_date, time.min)
        _logger.info("++++++++++Deadline date time: %s------------Lead date time : %s" % (deadline_date, self.lead_days_date))
        return lead_date

    def _get_orderpoint_action(self):
        """Create manual orderpoints for missing product in each warehouses. It also removes
        orderpoints that have been replenish. In order to do it:
        - It uses the report.stock.quantity to find missing quantity per product/warehouse
        - It checks if orderpoint already exist to refill this location.
        - It checks if it exists other sources (e.g RFQ) tha refill the warehouse.
        - It creates the orderpoints for missing quantity that were not refill by an upper option.

        return replenish report ir.actions.act_window
        """
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_orderpoint_replenish")
        action['context'] = self.env.context
        # Search also with archived ones to avoid to trigger product_location_check SQL constraints later
        # It means that when there will be a archived orderpoint on a location + product, the replenishment
        # report won't take in account this location + product and it won't create any manual orderpoint
        # In master: the active field should be remove
        orderpoints = self.env['stock.warehouse.orderpoint'].with_context(active_test=False).search([])
        # Remove previous automatically created orderpoint that has been refilled.
        orderpoints_removed = orderpoints._unlink_processed_orderpoints()
        orderpoints = orderpoints - orderpoints_removed
        to_refill = defaultdict(float)
        all_product_ids = self._get_orderpoint_products().ids
        all_replenish_location_ids = self.env['stock.location'].search([('replenish_location', '=', True)])
        ploc_per_day = defaultdict(set)
        # For each replenish location get products with negative virtual_available aka forecast
        for products in map(self.env['product.product'].browse, split_every(5000, all_product_ids)):
            for loc in all_replenish_location_ids:
                quantities = products.with_context(location=loc.id).mapped('virtual_available')
                for product, quantity in zip(products, quantities):
                    if float_compare(quantity, 0, precision_rounding=product.uom_id.rounding) >= 0:
                        continue
                    # group product by lead_days and location in order to read virtual_available
                    # in batch
                    rules = product._get_rules_from_location(loc)
                    lead_days = rules.with_context(bypass_delay_description=True)._get_lead_days(product)[0]
                    ploc_per_day[(lead_days, loc)].add(product.id)
            products.invalidate_recordset()

        # recompute virtual_available with lead days
        today = fields.datetime.now().replace(hour=23, minute=59, second=59)
        for (days, loc), product_ids in ploc_per_day.items():
            products = self.env['product.product'].browse(product_ids)
            qties = products.with_context(
                location=loc.id,
############# "to_date" is commented out by PPTS to avoid Forcasted quantity based on lead time.#################
                # to_date=today + relativedelta.relativedelta(days=days)


            ).read(['virtual_available'])
            for qty in qties:
                if float_compare(qty['virtual_available'], 0, precision_rounding=product.uom_id.rounding) < 0:
                    to_refill[(qty['id'], loc.id)] = qty['virtual_available']
            products.invalidate_recordset()
        if not to_refill:
            return action

        # Remove incoming quantity from other origin than moves (e.g RFQ)
        product_ids, location_ids = zip(*to_refill)
        qty_by_product_loc, dummy = self.env['product.product'].browse(product_ids)._get_quantity_in_progress(location_ids=location_ids)
        rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        # Group orderpoint by product-location
        orderpoint_by_product_location = self.env['stock.warehouse.orderpoint']._read_group(
            [('id', 'in', orderpoints.ids)],
            ['product_id', 'location_id', 'qty_to_order:sum'],
            ['product_id', 'location_id'], lazy=False)
        orderpoint_by_product_location = {
            (record.get('product_id')[0], record.get('location_id')[0]): record.get('qty_to_order')
            for record in orderpoint_by_product_location
        }
        for (product, location), product_qty in to_refill.items():
            qty_in_progress = qty_by_product_loc.get((product, location)) or 0.0
            qty_in_progress += orderpoint_by_product_location.get((product, location), 0.0)
            # Add qty to order for other orderpoint under this location.
            if not qty_in_progress:
                continue
            to_refill[(product, location)] = product_qty + qty_in_progress
        to_refill = {k: v for k, v in to_refill.items() if float_compare(
            v, 0.0, precision_digits=rounding) < 0.0}

        # With archived ones to avoid `product_location_check` SQL constraints
        orderpoint_by_product_location = self.env['stock.warehouse.orderpoint'].with_context(active_test=False)._read_group(
            [('id', 'in', orderpoints.ids)],
            ['product_id', 'location_id', 'ids:array_agg(id)'],
            ['product_id', 'location_id'], lazy=False)
        orderpoint_by_product_location = {
            (record.get('product_id')[0], record.get('location_id')[0]): record.get('ids')[0]
            for record in orderpoint_by_product_location
        }

        orderpoint_values_list = []
        for (product, location_id), product_qty in to_refill.items():
            orderpoint_id = orderpoint_by_product_location.get((product, location_id))
            if orderpoint_id:
                self.env['stock.warehouse.orderpoint'].browse(orderpoint_id).qty_forecast += product_qty
            else:
                orderpoint_values = self.env['stock.warehouse.orderpoint']._get_orderpoint_values(product, location_id)
                warehouse_id = self.env['stock.location'].browse(location_id).warehouse_id
                orderpoint_values.update({
                    'name': _('Replenishment Report'),
                    'warehouse_id': warehouse_id.id,
                    'company_id': warehouse_id.company_id.id,
                })
                orderpoint_values_list.append(orderpoint_values)

        orderpoints = self.env['stock.warehouse.orderpoint'].with_user(SUPERUSER_ID).create(orderpoint_values_list)
        for orderpoint in orderpoints:
            orderpoint._set_default_route_id()
            orderpoint.qty_multiple = orderpoint._get_qty_multiple_to_order()
        return action

    def _get_product_context(self, visibility_days=0):
        """Used to call `virtual_available` when running an orderpoint."""
        self.ensure_one()

        # "to_date" commented out by PPTS to avoid Forcasted quantity based on lead time.
        return {
            # 'location': False,
            'location': self.location_id.id,
            # 'to_date': datetime.combine(self.lead_days_date + relativedelta.relativedelta(days=visibility_days), time.max)
        }
    
    # @api.depends('product_id', 'location_id', 'product_id.stock_move_ids', 'product_id.stock_move_ids.state',
    #              'product_id.stock_move_ids.date', 'product_id.stock_move_ids.product_uom_qty')
    # def _compute_qty(self):
    #     orderpoints_contexts = defaultdict(lambda: self.env['stock.warehouse.orderpoint'])
    #     for orderpoint in self:
    #         if not orderpoint.product_id or not orderpoint.location_id:
    #             orderpoint.qty_on_hand = False
    #             orderpoint.qty_forecast = False
    #             continue
    #         orderpoint_context = orderpoint._get_product_context()
    #         product_context = frozendict({**orderpoint_context})
    #         orderpoints_contexts[product_context] |= orderpoint
    #     for orderpoint_context, orderpoints_by_context in orderpoints_contexts.items():
    #         products_qty = {
    #             p['id']: p for p in orderpoints_by_context.product_id.read(['qty_available', 'virtual_available'])
    #         }
    #         products_qty_in_progress = orderpoints_by_context._quantity_in_progress()
    #         for orderpoint in orderpoints_by_context:
    #             orderpoint.qty_on_hand = products_qty[orderpoint.product_id.id]['qty_available']
    #             orderpoint.qty_forecast = products_qty[orderpoint.product_id.id]['virtual_available'] + products_qty_in_progress[orderpoint.id]


