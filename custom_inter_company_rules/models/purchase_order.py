# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
# from odoo.exceptions import Warning


class purchase_order(models.Model):
    _inherit = "purchase.order"

    def inter_company_create_sale_order(self, company):
        """ Create a Sales Order from the current PO (self)
            Note : In this method, reading the current PO is done as sudo, and the creation of the derived
            SO as intercompany_user, minimizing the access right required for the trigger user.
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        self = self.with_context(force_company=company.id)
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']

        # find user for creating and validation SO/PO from partner company
        intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
        if not intercompany_uid:
            raise Warning(_('Provide at least one user for inter company relation for % ') % company.name)
        # check intercompany user access rights
        if not SaleOrder.with_user(intercompany_uid).check_access_rights('create', raise_exception=False):
            raise Warning(_("Inter company user of company %s doesn't have enough access rights") % company.name)

        for rec in self:
            if rec.company_id.id in company.allowed_company_ids.ids:
                # check pricelist currency should be same with SO/PO document
                company_partner = rec.company_id.partner_id.with_user(intercompany_uid)
                if rec.currency_id.id != company_partner.property_product_pricelist.currency_id.id:
                    raise Warning(
                        _('You cannot create SO from PO because sale price list currency is different than purchase price list currency.')
                        + '\n'
                        + _('The currency of the SO is obtained from the pricelist of the company partner.')
                        + '\n\n ({} {}, {} {}, {} {} (ID: {}))'.format(
                            _('SO currency:'), company_partner.property_product_pricelist.currency_id.name,
                            _('Pricelist:'), company_partner.property_product_pricelist.display_name,
                            _('Partner:'), company_partner.display_name, company_partner.id,
                        )
                    )

                # create the SO and generate its lines from the PO lines
                # read it as sudo, because inter-compagny user can not have the access right on PO
                sale_order_data = rec.sudo()._prepare_sale_order_data(
                    rec.name, company_partner, company,
                    rec.dest_address_id and rec.dest_address_id.id or False)
                sale_order = SaleOrder.with_user(intercompany_uid).create(sale_order_data)
                # lines are browse as sudo to access all data required to be copied on SO line (mainly for company dependent field like taxes)
                for line in rec.order_line.sudo():
                    so_line_vals = rec._prepare_sale_order_line_data(line, company, sale_order.id)
                    # TODO: create can be done in batch; this may be a performance bottleneck
                    SaleOrderLine.with_user(intercompany_uid).create(so_line_vals)

                # write vendor reference field on PO
                if not rec.partner_ref:
                    rec.partner_ref = sale_order.name

                #Validation of sales order
                if company.auto_validation:
                    sale_order.with_user(intercompany_uid).action_confirm()
