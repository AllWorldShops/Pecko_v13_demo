# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero

from collections import defaultdict
from odoo import api, fields, models, SUPERUSER_ID, _


class StockRule(models.Model):
    _inherit = "stock.rule"

    action = fields.Selection(
        selection_add=[("split_procurement", "Choose between MTS and MTO")]
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

    def _get_qty_available_for_mto_qty(self, product, product_location, product_uom):
        virtual_available = product_location.virtual_available
        return product.uom_id._compute_quantity(virtual_available, product_uom)

    def get_mto_qty_to_order(self, product, product_qty, product_uom, values):
        self.ensure_one()
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        src_location_id = self.mts_rule_id.location_src_id.id
        product_location = product.with_context(location=src_location_id)
        qty_available = self._get_qty_available_for_mto_qty(
            product, product_location, product_uom
        )
        if float_compare(qty_available, 0.0, precision_digits=precision) > 0:
            if (
                float_compare(qty_available, product_qty, precision_digits=precision)
                >= 0
            ):
                return 0.0
            else:
                return product_qty - qty_available
        return product_qty

    def _run_split_procurement(self, procurements):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for procurement, rule in procurements:
            domain = self.env["procurement.group"]._get_moves_to_assign_domain(
                procurement.company_id.id
            )
            needed_qty = rule.get_mto_qty_to_order(
                procurement.product_id,
                procurement.product_qty,
                procurement.product_uom,
                procurement.values,
            )
            if float_is_zero(needed_qty, precision_digits=precision):
                getattr(self.env["stock.rule"], "_run_%s" % rule.mts_rule_id.action)(
                    [(procurement, rule.mts_rule_id)]
                )
            elif (
                float_compare(
                    needed_qty, procurement.product_qty, precision_digits=precision
                )
                == 0.0
            ):
                getattr(self.env["stock.rule"], "_run_%s" % rule.mto_rule_id.action)(
                    [(procurement, rule.mto_rule_id)]
                )
            else:
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
                    group_domain, order="priority desc, date_expected asc"
                )
                moves_to_assign._action_assign()

                mto_procurement = procurement._replace(product_qty=needed_qty)
                getattr(self.env["stock.rule"], "_run_%s" % rule.mto_rule_id.action)(
                    [(mto_procurement, rule.mto_rule_id)]
                )
        return True


    @api.model
    def _run_manufacture(self, procurements):
        productions_values_by_company = defaultdict(list)
        for procurement, rule in procurements:
            if float_compare(procurement.product_qty, 0, precision_rounding=procurement.product_uom.rounding) <= 0:
                # If procurement contains negative quantity, don't create a MO that would be for a negative value.
                continue
            bom = rule._get_matching_bom(procurement.product_id, procurement.company_id, procurement.values)

            productions_values_by_company[procurement.company_id.id].append(rule._prepare_mo_vals(*procurement, bom))

        for company_id, productions_values in productions_values_by_company.items():
            # create the MO as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
            productions = self.env['mrp.production'].with_user(SUPERUSER_ID).sudo().with_company(company_id).with_delay().create(productions_values)
            productions.filtered(lambda p: (not p.orderpoint_id and p.move_raw_ids) or\
                (p.move_dest_ids.procure_method != 'make_to_order' and not p.move_raw_ids and not p.workorder_ids)).action_confirm()

            for production in productions:
                origin_production = production.move_dest_ids and production.move_dest_ids[0].raw_material_production_id or False
                orderpoint = production.orderpoint_id
                if orderpoint and orderpoint.create_uid.id == SUPERUSER_ID and orderpoint.trigger == 'manual':
                    production.message_post(
                        body=_('This production order has been created from Replenishment Report.'),
                        message_type='comment',
                        subtype_xmlid='mail.mt_note')
                elif orderpoint:
                    production.message_post_with_view(
                        'mail.message_origin_link',
                        values={'self': production, 'origin': orderpoint},
                        subtype_id=self.env.ref('mail.mt_note').id)
                elif origin_production:
                    production.message_post_with_view(
                        'mail.message_origin_link',
                        values={'self': production, 'origin': origin_production},
                        subtype_id=self.env.ref('mail.mt_note').id)
        return True