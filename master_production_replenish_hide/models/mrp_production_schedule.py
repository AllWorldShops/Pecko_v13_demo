from odoo import models, fields
from dateutil.relativedelta import relativedelta
from math import log10
from collections import defaultdict, namedtuple
from odoo.tools.date_utils import add, subtract
from odoo.tools.float_utils import float_round
from odoo.osv.expression import OR, AND
from collections import OrderedDict
import locale
locale.setlocale(locale.LC_ALL, '')





class MrpProductionSchedule(models.Model):
    _inherit = 'mrp.production.schedule'

    def get_production_schedule_view_state(self):

        company_id = self.env.company
        date_range = company_id._get_date_range()
        date_range_year_minus_1 = company_id._get_date_range(years=1)
        date_range_year_minus_2 = company_id._get_date_range(years=2)

        # We need to get the schedule that impact the schedules in self. Since
        # the state is not saved, it needs to recompute the quantity to
        # replenish of finished products. It will modify the indirect
        # demand and replenish_qty of schedules in self.
        schedules_to_compute = self.env['mrp.production.schedule'].browse(self.get_impacted_schedule()) | self

        # Dependencies between schedules
        indirect_demand_trees = schedules_to_compute._get_indirect_demand_tree()

        indirect_ratio_mps = schedules_to_compute._get_indirect_demand_ratio_mps(indirect_demand_trees)

        # Get the schedules that do not depends from other in first position in
        # order to compute the schedule state only once.
        indirect_demand_order = schedules_to_compute._get_indirect_demand_order(indirect_demand_trees)
        indirect_demand_qty = defaultdict(float)
        incoming_qty, incoming_qty_done = self._get_incoming_qty(date_range)
        outgoing_qty, outgoing_qty_done = self._get_outgoing_qty(date_range)
        dummy, outgoing_qty_year_minus_1 = self._get_outgoing_qty(date_range_year_minus_1)
        dummy, outgoing_qty_year_minus_2 = self._get_outgoing_qty(date_range_year_minus_2)
        read_fields = [
            'forecast_target_qty',
            'min_to_replenish_qty',
            'max_to_replenish_qty',
            'product_id',

        ]
        if self.env.user.has_group('stock.group_stock_multi_warehouses'):
            read_fields.append('warehouse_id')
        if self.env.user.has_group('uom.group_uom'):
            read_fields.append('product_uom_id')
        production_schedule_states = schedules_to_compute.read(read_fields)
        production_schedule_states_by_id = {mps['id']: mps for mps in production_schedule_states}
        location_list = []
        for production_schedule in indirect_demand_order:
            # Bypass if the schedule is only used in order to compute indirect
            # demand.
            rounding = production_schedule.product_id.uom_id.rounding
            lead_time = production_schedule._get_lead_times()
            production_schedule_state = production_schedule_states_by_id[production_schedule['id']]
            if production_schedule in self:
                procurement_date = add(fields.Date.today(), days=lead_time)
                precision_digits = max(0, int(-(log10(production_schedule.product_uom_id.rounding))))
                production_schedule_state['precision_digits'] = precision_digits
                production_schedule_state['forecast_ids'] = []

            starting_inventory_qty = production_schedule.product_id.with_context(
                warehouse=production_schedule.warehouse_id.id).qty_available
            if len(date_range):
                starting_inventory_qty -= incoming_qty_done.get(
                    (date_range[0], production_schedule.product_id, production_schedule.warehouse_id), 0.0)
                starting_inventory_qty += outgoing_qty_done.get(
                    (date_range[0], production_schedule.product_id, production_schedule.warehouse_id), 0.0)

            for index, (date_start, date_stop) in enumerate(date_range):
                forecast_values = {}
                key = ((date_start, date_stop), production_schedule.product_id, production_schedule.warehouse_id)
                key_y_1 = (date_range_year_minus_1[index], *key[1:])
                key_y_2 = (date_range_year_minus_2[index], *key[1:])
                existing_forecasts = production_schedule.forecast_ids.filtered(
                    lambda p: p.date >= date_start and p.date <= date_stop)
                if production_schedule in self:
                    forecast_values['date_start'] = date_start
                    forecast_values['date_stop'] = date_stop
                    forecast_values['incoming_qty'] = float_round(
                        incoming_qty.get(key, 0.0) + incoming_qty_done.get(key, 0.0), precision_rounding=rounding)
                    forecast_values['outgoing_qty'] = float_round(
                        outgoing_qty.get(key, 0.0) + outgoing_qty_done.get(key, 0.0), precision_rounding=rounding)
                    forecast_values['outgoing_qty_year_minus_1'] = float_round(
                        outgoing_qty_year_minus_1.get(key_y_1, 0.0), precision_rounding=rounding)
                    forecast_values['outgoing_qty_year_minus_2'] = float_round(
                        outgoing_qty_year_minus_2.get(key_y_2, 0.0), precision_rounding=rounding)

                forecast_values['indirect_demand_qty'] = float_round(indirect_demand_qty.get(key, 0.0),
                                                                     precision_rounding=rounding, rounding_method='UP')
                replenish_qty_updated = False
                if existing_forecasts:
                    forecast_values['forecast_qty'] = float_round(sum(existing_forecasts.mapped('forecast_qty')),
                                                                  precision_rounding=rounding)
                    forecast_values['replenish_qty'] = float_round(sum(existing_forecasts.mapped('replenish_qty')),
                                                                   precision_rounding=rounding)

                    # Check if the to replenish quantity has been manually set or
                    # if it needs to be computed.
                    replenish_qty_updated = any(existing_forecasts.mapped('replenish_qty_updated'))
                    forecast_values['replenish_qty_updated'] = replenish_qty_updated
                else:
                    forecast_values['forecast_qty'] = 0.0

                if not replenish_qty_updated:
                    replenish_qty = production_schedule._get_replenish_qty(
                        starting_inventory_qty - forecast_values['forecast_qty'] - forecast_values[
                            'indirect_demand_qty'])
                    forecast_values['replenish_qty'] = float_round(replenish_qty, precision_rounding=rounding)
                    forecast_values['replenish_qty_updated'] = False

                forecast_values['starting_inventory_qty'] = float_round(starting_inventory_qty,
                                                                        precision_rounding=rounding)
                forecast_values['safety_stock_qty'] = float_round(
                    starting_inventory_qty - forecast_values['forecast_qty'] - forecast_values['indirect_demand_qty'] +
                    forecast_values['replenish_qty'], precision_rounding=rounding)

                if production_schedule in self:
                    production_schedule_state['forecast_ids'].append(forecast_values)
                starting_inventory_qty = forecast_values['safety_stock_qty']
                if not forecast_values['replenish_qty']:
                    continue
                # Set the indirect demand qty for children schedules.
                for (product, ratio) in indirect_ratio_mps[
                    (production_schedule.warehouse_id, production_schedule.product_id)].items():
                    related_date = max(subtract(date_start, days=lead_time), fields.Date.today())
                    index = next(i for i, (dstart, dstop) in enumerate(date_range) if
                                 related_date <= dstart or (related_date >= dstart and related_date <= dstop))
                    related_key = (date_range[index], product, production_schedule.warehouse_id)
                    indirect_demand_qty[related_key] += ratio * forecast_values['replenish_qty']
            location = self.env['res.company'].search([('id', '=', self.company_id.id)])
            quantity_total = 0
            for loc in location.location_ids:
                product = production_schedule.product_id
                quantity_check = self.env['stock.quant'].search(
                    [('location_id', 'in', loc.ids), ('product_id', '=', product.id)])
                for qty in quantity_check:
                    quantity_total += qty.quantity
            rounded_value = round(quantity_total, 4)
            forecast_values['onhand_quantity'] = f'{rounded_value:n}'
            forecast_values['mpn_supplier_no'] =  production_schedule.product_id.x_studio_field_qr3ai

            if production_schedule in self:
                # The state is computed after all because it needs the final
                # quantity to replenish.
                forecasts_state = production_schedule._get_forecasts_state(production_schedule_states_by_id, date_range,
                                                                           procurement_date)
                forecasts_state = forecasts_state[production_schedule.id]
                for index, forecast_state in enumerate(forecasts_state):
                    production_schedule_state['forecast_ids'][index].update(forecast_state)

                # The purpose is to hide indirect demand row if the schedule do not
                # depends from another.
                has_indirect_demand = any(
                    forecast['indirect_demand_qty'] != 0 for forecast in production_schedule_state['forecast_ids'])
                production_schedule_state['has_indirect_demand'] = has_indirect_demand
        return [p for p in production_schedule_states if p['id'] in self.ids]
