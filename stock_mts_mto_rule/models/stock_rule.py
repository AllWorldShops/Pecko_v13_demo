# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero

from collections import defaultdict
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import groupby
from dateutil.relativedelta import relativedelta


class StockRule(models.Model):
    _inherit = "stock.rule"

    action = fields.Selection(
        selection_add=[("split_procurement", "Choose between MTS and MTO")],
        ondelete={"split_procurement": "cascade"},
    )
    mts_rule_id = fields.Many2one("stock.rule", string="MTS Rule", check_company=True)
    mto_rule_id = fields.Many2one("stock.rule", string="MTO Rule", check_company=True)

    @api.constrains("action", "mts_rule_id", "mto_rule_id")
    def _check_mts_mto_rule(self):
        for rule in self:
            if rule.action == "split_procurement":
                if not rule.mts_rule_id or not rule.mto_rule_id:
                    msg = _(
                        "No MTS or MTO rule configured on procurement " "rule: %s!"
                    ) % (rule.name,)
                    raise ValidationError(msg)
                if (
                    rule.mts_rule_id.location_src_id.id
                    != rule.mto_rule_id.location_src_id.id
                ):
                    msg = _(
                        "Inconsistency between the source locations of "
                        "the mts and mto rules linked to the procurement "
                        "rule: %s! It should be the same."
                    ) % (rule.name,)
                    raise ValidationError(msg)

    def get_mto_qty_to_order(self, product, product_qty, product_uom, values):
        self.ensure_one()
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        src_location_id = self.mts_rule_id.location_src_id.id
        product_location = product.with_context(location=src_location_id)
        virtual_available = product_location.virtual_available
        qty_available = product.uom_id._compute_quantity(virtual_available, product_uom)
        print('qty_available',qty_available)
        if float_compare(qty_available, 0.0, precision_digits=precision) > 0:
            print('@@@@@@@@@@')
            if (
                float_compare(qty_available, product_qty, precision_digits=precision)
                >= 0
            ):
                return 0.0
            else:
                ss = product.seller_ids[0] if product.seller_ids else ''
                print('sssssssssss',ss)
                if ss:
                    print('sssssssssss',ss.min_qty)
                    print('product_qty + qty_available',product_qty + qty_available)
                    if product_qty + qty_available <= ss.min_qty:
                        print('1111111111111')
                        qty = ss.min_qty
                    
                    else:
                        print('222222222222')
                        qty = product_qty - qty_available
                else:
                    print('222222222222')
                    qty = product_qty - qty_available
                return qty

        else:
            print('################')
            ss = product.seller_ids[0] if product.seller_ids else ''
            print('sssssssssss',ss)
            # print('sssssssssss',ss.min_qty)
            print('product_qty + qty_available',product_qty + qty_available)
            if ss:
                if qty_available >= 0:
                    if product_qty + qty_available <= ss.min_qty:
                        print('1111111111111')
                        qty = ss.min_qty
                    else:
                        qty = ss.min_qty * product_qty + qty_available
                    
                else:
                    print('222222222222')
                    if product_qty - qty_available > ss.min_qty:
                        return ss.min_qty
                    
                    else:
                        qty = 0
                return qty
            else:
                return product_qty - qty_available

        return product_qty

    def _run_split_procurement(self, procurements):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for procurement, rule in procurements:
            print('procurements',procurements)
            print('procurement.product_qty',procurement.product_qty)
            domain = self.env["procurement.group"]._get_moves_to_assign_domain(
                procurement.company_id.id
            )
            needed_qty = rule.get_mto_qty_to_order(
                procurement.product_id,
                procurement.product_qty,
                procurement.product_uom,
                procurement.values,
            )
            print('needed_qty',needed_qty)
            if float_is_zero(needed_qty, precision_digits=precision):
                print('aaaaaaaaaaaaaaaa')
                getattr(self.env["stock.rule"], "_run_%s" % rule.mts_rule_id.action)(
                    [(procurement, rule.mts_rule_id)]
                )
            elif (
                float_compare(
                    needed_qty, procurement.product_qty, precision_digits=precision
                )
                == 0.0
            ):
                print('bbbbbbbbbbbbbbbbb')
                print('bbbbbbbbbbbbbbbbb',rule.mto_rule_id.action)
                getattr(self.env["stock.rule"], "_run_%s" % rule.mto_rule_id.action)(
                    [(procurement, rule.mto_rule_id)]
                )
            else:
                print('ccccccccccccccccc')
                mts_qty = procurement.product_qty - needed_qty
                mts_procurement = procurement._replace(product_qty=mts_qty)
                getattr(self.env["stock.rule"], "_run_%s" % rule.mts_rule_id.action)(
                    [(mts_procurement, rule.mts_rule_id)]
                )

                # Search all confirmed stock_moves of mts_procuremet and assign them
                # to adjust the product's free qty
                group_id = mts_procurement.values.get("group_id")
                group_domain = expression.AND(
                    [domain, [("group_id", "=", group_id.id)]]
                )
                moves_to_assign = self.env["stock.move"].search(
                    group_domain, order="priority desc, date asc"
                )
                moves_to_assign._action_assign()

                mto_procurement = procurement._replace(product_qty=needed_qty)
                getattr(self.env["stock.rule"], "_run_%s" % rule.mto_rule_id.action)(
                    [(mto_procurement, rule.mto_rule_id)]
                )
        
        return True


    @api.model
    def _run_buy(self, procurements):
        
        procurements_by_po_domain = defaultdict(list)
        errors = []
        for procurement, rule in procurements:

            # Get the schedule date in order to find a valid seller
            procurement_date_planned = fields.Datetime.from_string(procurement.values['date_planned'])

            supplier = False
            if procurement.values.get('supplierinfo_id'):
                supplier = procurement.values['supplierinfo_id']
            else:
                supplier = procurement.product_id.with_company(procurement.company_id.id)._select_seller(
                    partner_id=procurement.values.get("supplierinfo_name"),
                    quantity=procurement.product_qty,
                    date=procurement_date_planned.date(),
                    uom_id=procurement.product_uom)

            # Fall back on a supplier for which no price may be defined. Not ideal, but better than
            # blocking the user.
            supplier = supplier or procurement.product_id._prepare_sellers(False).filtered(
                lambda s: not s.company_id or s.company_id == procurement.company_id
            )[:1]

            if not supplier:
                msg = _('There is no matching vendor price to generate the purchase order for product %s (no vendor defined, minimum quantity not reached, dates not valid, ...). Go on the product form and complete the list of vendors.') % (procurement.product_id.display_name)
                errors.append((procurement, msg))

            partner = supplier.partner_id
            # we put `supplier_info` in values for extensibility purposes
            procurement.values['supplier'] = supplier
            procurement.values['propagate_cancel'] = rule.propagate_cancel

            domain = rule._make_po_get_domain(procurement.company_id, procurement.values, partner)
            procurements_by_po_domain[domain].append((procurement, rule))

        if errors:
            raise ProcurementException(errors)

        for domain, procurements_rules in procurements_by_po_domain.items():
            # Get the procurements for the current domain.
            # Get the rules for the current domain. Their only use is to create
            # the PO if it does not exist.
            procurements, rules = zip(*procurements_rules)

            # Get the set of procurement origin for the current domain.
            origins = set([p.origin for p in procurements])
            # Check if a PO exists for the current domain.
            print('domain',domain)
            po = self.env['purchase.order'].sudo().search([dom for dom in domain], limit=1)
            print('po',po)
            company_id = procurements[0].company_id

            # PPTS comment the below code for PO split concept requested by Suresh on 08.05.2023
            # if not po or po:
            if not po or po:
                positive_values = [p.values for p in procurements if float_compare(p.product_qty, 0.0, precision_rounding=p.product_uom.rounding) >= 0]
                if positive_values:
                    # We need a rule to generate the PO. However the rule generated
                    # the same domain for PO and the _prepare_purchase_order method
                    # should only uses the common rules's fields.
                    vals = rules[0]._prepare_purchase_order(company_id, origins, positive_values)
                    # The company_id is the same for all procurements since
                    # _make_po_get_domain add the company in the domain.
                    # We use SUPERUSER_ID since we don't want the current user to be follower of the PO.
                    # Indeed, the current user may be a user without access to Purchase, or even be a portal user.
                    po = self.env['purchase.order'].with_company(company_id).with_user(SUPERUSER_ID).create(vals)
            else:
                # If a purchase order is found, adapt its `origin` field.
                if po.origin:
                    missing_origins = origins - set(po.origin.split(', '))
                    if missing_origins:
                        po.write({'origin': po.origin + ', ' + ', '.join(missing_origins)})
                else:
                    po.write({'origin': ', '.join(origins)})

            procurements_to_merge = self._get_procurements_to_merge(procurements)
            procurements = self._merge_procurements(procurements_to_merge)

            po_lines_by_product = {}
            grouped_po_lines = groupby(po.order_line.filtered(lambda l: not l.display_type and l.product_uom == l.product_id.uom_po_id), key=lambda l: l.product_id.id)
            for product, po_lines in grouped_po_lines:
                po_lines_by_product[product] = self.env['purchase.order.line'].concat(*po_lines)
            po_line_values = []
            for procurement in procurements:
                po_lines = po_lines_by_product.get(procurement.product_id.id, self.env['purchase.order.line'])
                po_line = po_lines._find_candidate(*procurement)

                if po_line:
                    # If the procurement can be merge in an existing line. Directly
                    # write the new values on it.
                    vals = self._update_purchase_order_line(procurement.product_id,
                        procurement.product_qty, procurement.product_uom, company_id,
                        procurement.values, po_line)
                    po_line.write(vals)
                else:
                    if float_compare(procurement.product_qty, 0, precision_rounding=procurement.product_uom.rounding) <= 0:
                        # If procurement contains negative quantity, don't create a new line that would contain negative qty
                        continue
                    # If it does not exist a PO line for current procurement.
                    # Generate the create values for it and add it to a list in
                    # order to create it in batch.
                    partner = procurement.values['supplier'].partner_id
                    po_line_values.append(self.env['purchase.order.line']._prepare_purchase_order_line_from_procurement(
                        procurement.product_id, procurement.product_qty,
                        procurement.product_uom, procurement.company_id,
                        procurement.values, po))
                    # Check if we need to advance the order date for the new line
                    order_date_planned = procurement.values['date_planned'] - relativedelta(
                        days=procurement.values['supplier'].delay)
                    if fields.Date.to_date(order_date_planned) < fields.Date.to_date(po.date_order):
                        po.date_order = order_date_planned
            self.env['purchase.order.line'].sudo().create(po_line_values)

    # PPTS using this function for MO schedule date changes requested by Suresh on 12.05.2023 starts
    # we have added product_qty paramenter in this function, the parameter passed to _get_date_planned function 
    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values, bom):
        date_planned = self._get_date_planned(product_id, company_id, values, product_qty)
        date_deadline = values.get('date_deadline') or date_planned + relativedelta(days=product_id.produce_delay)

        mo_values = {
            'origin': origin,
            'product_id': product_id.id,
            'product_description_variants': values.get('product_description_variants'),
            'product_qty': product_uom._compute_quantity(product_qty, bom.product_uom_id) if bom else product_qty,
            'product_uom_id': bom.product_uom_id.id if bom else product_uom.id,
            'location_src_id': self.location_src_id.id or self.picking_type_id.default_location_src_id.id or location_dest_id.id,
            'location_dest_id': location_dest_id.id,
            'bom_id': bom.id,
            'date_deadline': date_deadline,
            'date_planned_start': date_planned,
            'date_planned_finished': fields.Datetime.from_string(values['date_planned']),
            'procurement_group_id': False,
            'propagate_cancel': self.propagate_cancel,
            'orderpoint_id': values.get('orderpoint_id', False) and values.get('orderpoint_id').id,
            'picking_type_id': self.picking_type_id.id or values['warehouse_id'].manu_type_id.id,
            'company_id': company_id.id,
            'move_dest_ids': values.get('move_dest_ids') and [(4, x.id) for x in values['move_dest_ids']] or False,
            'user_id': False,
        }
        # Use the procurement group created in _run_pull mrp override
        # Preserve the origin from the original stock move, if available
        if location_dest_id.warehouse_id.manufacture_steps == 'pbm_sam' and values.get('move_dest_ids') and values.get('group_id') and values['move_dest_ids'][0].origin != values['group_id'].name:
            origin = values['move_dest_ids'][0].origin
            mo_values.update({
                'name': values['group_id'].name,
                'procurement_group_id': values['group_id'].id,
                'origin': origin,
            })
        return mo_values

    def _get_date_planned(self, product_id, company_id, values, product_qty):
        
        format_date_planned = fields.Datetime.from_string(values['date_planned'])
        # PPTS comment the below code for MO schedule date changes requested by Suresh on 12.05.2023
        # date_planned = format_date_planned - relativedelta(days=product_id.produce_delay)
        date_planned = format_date_planned - relativedelta(days=product_id.days_to_prepare_mo * product_qty)
        if date_planned == format_date_planned:
            date_planned = date_planned - relativedelta(hours=1)
        return date_planned

    # PPTS using this function for MO schedule date changes requested by Suresh on 12.05.2023 ends