from odoo import api, fields, models
from datetime import datetime,date
from dateutil.relativedelta import relativedelta



class StockRule(models.Model):
    _inherit = 'stock.rule'

    #Override to add active False during Purchase creation from reordering Rule
    def _prepare_purchase_order(self, company_id, origins, values):
        """ Create a purchase order for procuremets that share the same domain
        returned by _make_po_get_domain.
        params values: values of procurements
        params origins: procuremets origins to write on the PO
        """
        purchase_date = min([fields.Datetime.from_string(value['date_planned']) - relativedelta(days=int(value['supplier'].delay)) for value in values])
        # Since the procurements are grouped if they share the same domain for
        # PO but the PO does not exist. In this case it will create the PO from
        # the common procurements values. The common values are taken from an
        # arbitrary procurement. In this case the first.
        values = values[0]
        partner = values['supplier'].partner_id

        fpos = self.env['account.fiscal.position'].with_company(company_id)._get_fiscal_position(partner)

        gpo = self.group_propagation_option
        group = (gpo == 'fixed' and self.group_id.id) or \
                (gpo == 'propagate' and values.get('group_id') and values['group_id'].id) or False

        return {
            'partner_id': partner.id,
            'user_id': False,
            'picking_type_id': self.picking_type_id.id,
            'company_id': company_id.id,
            'currency_id': partner.with_company(company_id).property_purchase_currency_id.id or company_id.currency_id.id,
            'dest_address_id': values.get('partner_id', False),
            'origin': ', '.join(origins),
            'payment_term_id': partner.with_company(company_id).property_supplier_payment_term_id.id,
            'date_order': purchase_date,
            'fiscal_position_id': fpos.id,
            'group_id': group,
            'active':False
        }
        