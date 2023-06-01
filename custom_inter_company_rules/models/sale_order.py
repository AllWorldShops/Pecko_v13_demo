# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
# from odoo.enterprise_13.models.sale_order import sale_order


class SaleOrder(models.Model):

    _inherit = "sale.order"


    def inter_company_create_purchase_order(self, company):
        """ Create a Purchase Order from the current SO (self)
            Note : In this method, reading the current SO is done as sudo, and the creation of the derived
            PO as intercompany_user, minimizing the access right required for the trigger user
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        self = self.with_context(force_company=company.id, company_id=company.id)
        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']
        
        for rec in self:
            if rec.company_id.id in company.allowed_company_ids.ids:
                company_partner = rec.company_id and rec.company_id.partner_id or False
                if not company or not company_partner.id:
                    continue

                # find user for creating and validating SO/PO from company
                intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
                if not intercompany_uid:
                    raise Warning(_('Provide one user for intercompany relation for % ') % company.name)
                # check intercompany user access rights
                if not PurchaseOrder.with_user(intercompany_uid).check_access_rights('create', raise_exception=False):
                    raise Warning(_("Inter company user of company %s doesn't have enough access rights") % company.name)

                # create the PO and generate its lines from the SO
                # read it as sudo, because inter-compagny user can not have the access right on PO
                po_vals = rec.sudo()._prepare_purchase_order_data(company, company_partner)
                purchase_order = PurchaseOrder.with_user(intercompany_uid).create(po_vals)
                for line in rec.order_line.sudo().filtered(lambda l: not l.display_type):
                    po_line_vals = rec._prepare_purchase_order_line_data(line, rec.date_order,
                        purchase_order.id, company)
                    # TODO: create can be done in batch; this may be a performance bottleneck
                    PurchaseOrderLine.with_user(intercompany_uid).create(po_line_vals)

                # write customer reference field on SO
                if not rec.client_order_ref:
                    rec.client_order_ref = purchase_order.name

                # auto-validate the purchase order if needed
                if company.auto_validation:
                    purchase_order.with_user(intercompany_uid).button_confirm()

