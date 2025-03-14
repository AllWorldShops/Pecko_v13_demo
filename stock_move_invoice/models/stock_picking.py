# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import requests
import json
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    invoice_count = fields.Integer(string='Invoices', compute='_compute_invoice_count')
    operation_code = fields.Selection(related='picking_type_id.code')
    is_return = fields.Boolean()
    invoice_created = fields.Boolean()
    invoice_status = fields.Selection(related='sale_id.invoice_status', string='Invoice Status', store=True, readonly=True)

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking_id in self:
            # print(picking_id.state, "picking_id.state")
            if picking_id.state == 'done' and picking_id.picking_type_id.code == 'outgoing' and picking_id.sale_id:
                picking_id.create_invoice()
            if picking_id.state == 'done' and picking_id.picking_type_id.code == 'incoming' and 'Return' in str(picking_id.origin) and picking_id.sale_id:
                picking_id.create_customer_credit()

            # Detrack API starts
            if picking_id.state == 'done' and picking_id.picking_type_id.code == 'outgoing' and picking_id.sale_id and picking_id.company_id.country_id.code in ['SG', 'MY']:
                url = self.env['url.config'].search([('code', '=', 'DO'),('active', '=', True)], limit=1)
                if url:
                    headers = {'Content-Type': 'application/json', 'X-API-KEY': '2fe3ddf50048acc2231e184f230750ab59dcb9474bbaba6b'}
                    street1 = (picking_id.partner_id.street + ", " if picking_id.partner_id.street else "")
                    street2 = (picking_id.partner_id.street2  if picking_id.partner_id.street2 else "")
                    city = (picking_id.partner_id.city +  ", " if picking_id.partner_id.city else "")
                    state = (picking_id.partner_id.state_id.name + ", " if picking_id.partner_id.state_id else "")
                    country = (picking_id.partner_id.country_id.name  if picking_id.partner_id.country_id else "")
                    delivery_address = picking_id.partner_id.name + ", \n" + street1 + street2 + "\n" + city + state + country
                    driver = str(picking_id.driver_id.name) if picking_id.driver_id else ""
                    move_items = []
                    for line in picking_id.move_line_ids_without_package:
                        move_items.append({
                            'sku' : line.product_id.default_code,
                            'description': str(line.part_no),
                            'quantity': str(line.qty_done),
                        })
                    data = {
                        "data": {
                            "type": "Delivery",
                            "do_number": picking_id.name,
                            "date": str(picking_id.date_done.date()),
                            "address": delivery_address,
                            'assign_to': driver,
                            "items": move_items
                            }
                        }
                    data_json = json.dumps(data)
                    url = str(url.name)
                    try:
                        r = requests.post(url=url, headers=headers, data=data_json)
                    except Exception as e:
                        _logger.info("---------Exception Occured ---------: %s", str(e))
            # Detramck API ends

        return res

    def _compute_invoice_count(self):
        """This compute function used to count the number of invoice for the picking"""
        for picking_id in self:
            move_ids = picking_id.env['account.move'].search([('picking_id', '=', picking_id.id)])
            if move_ids:
                self.invoice_count = len(move_ids)
            else:
                self.invoice_count = 0

    def create_invoice(self):
        """This is the function for creating customer invoice
        from the picking"""
        for picking_id in self:
            if picking_id.invoice_status not in ['invoiced', 'no']:
                journal_id = False
                journal_id = self.env['account.journal'].search([('type','=','sale'),('name','=','Sales'),('company_id','=',picking_id.company_id.id)],limit=1).id
                invoice_line_list = []
                if picking_id.move_line_ids_without_package:
                    for move_line in picking_id.move_line_ids_without_package:
                        if move_line.move_id.sale_line_id:
                            for move in move_line.move_id:
                                vals = move.sale_line_id._prepare_invoice_line()
                                vals['position_no'] = move.position_no
                                if move.sale_line_id.qty_to_invoice != move_line.qty_done:
                                    vals['quantity'] = move_line.qty_done if move_line.product_id.uom_id.id == move_line.product_id.uom_po_id.id else move_line.qty_done / move.sale_line_id.product_uom.factor_inv
                                invoice_line_list.append((0, 0, vals))
                else:
                    for move in picking_id.move_ids_without_package:
                        if move.sale_line_id:
                            vals = move.sale_line_id._prepare_invoice_line()
                            vals['position_no'] = move.position_no
                            if move.sale_line_id.qty_to_invoice != move.quantity_done:
                                vals['quantity'] = move.quantity_done if move.product_id.uom_id.id == move.product_id.uom_po_id.id else move.quantity_done / move.sale_line_id.product_uom.factor_inv
                            invoice_line_list.append((0, 0, vals))
                if invoice_line_list:
                    invoice = picking_id.sale_id._prepare_invoice()
                    invoice['picking_id'] = picking_id.id
                    invoice['customer_po_no'] = picking_id.customer_po_no
                    invoice['do_name'] = picking_id.name
                    invoice['journal_id'] = journal_id
                    # invoice['invoice_origin'] = picking_id.sale_id.name,
                    invoice['invoice_line_ids'] = invoice_line_list
                    invoices = self.env['account.move'].create(invoice)
                    picking_id.invoice_created = True
                    return invoices

    # def create_bill(self):
    #     """This is the function for creating vendor bill
    #             from the picking"""
    #     for picking_id in self:
    #         current_user = self.env.uid
    #         if picking_id.picking_type_id.code == 'incoming':
    #             vendor_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
    #                 'stock_move_invoice.vendor_journal_id') or False
    #             if not vendor_journal_id:
    #                 raise UserError(_("Please configure the journal from the settings."))
    #             invoice_line_list = []
    #             for move_ids_without_package in picking_id.move_ids_without_package:
    #                 vals = (0, 0, {
    #                     'name': move_ids_without_package.description_picking,
    #                     'product_id': move_ids_without_package.product_id.id,
    #                     'price_unit': move_ids_without_package.product_id.lst_price,
    #                     'account_id': move_ids_without_package.product_id.property_account_income_id.id if move_ids_without_package.product_id.property_account_income_id
    #                     else move_ids_without_package.product_id.categ_id.property_account_income_categ_id.id,
    #                     'tax_ids': [(6, 0, [picking_id.company_id.account_purchase_tax_id.id])],
    #                     'quantity': move_ids_without_package.quantity_done,
    #                 })
    #                 invoice_line_list.append(vals)
    #             invoice = picking_id.env['account.move'].create({
    #                 'type': 'in_invoice',
    #                 'invoice_origin': picking_id.name,
    #                 'invoice_user_id': current_user,
    #                 # 'narration': picking_id.name,
    #                 'partner_id': picking_id.partner_id.id,
    #                 'currency_id': picking_id.env.user.company_id.currency_id.id,
    #                 'journal_id': int(vendor_journal_id),
    #                 'invoice_payment_ref': picking_id.name,
    #                 'picking_id': picking_id.id,
    #                 'invoice_line_ids': invoice_line_list
    #             })
    #             picking_id.invoice_created = True
    #             return invoice

    def create_customer_credit(self):
        """This is the function for creating customer credit note
                from the picking"""
        for picking_id in self:
            if picking_id.invoice_status not in ['invoiced', 'no']:

                invoice_line_list = []
                if picking_id.move_line_ids_without_package:
                    for move_line in picking_id.move_line_ids_without_package:
                        if move_line.move_id.sale_line_id:
                            for move in move_line.move_id:
                                vals = move.sale_line_id._prepare_invoice_line()
                                vals['position_no'] = move.position_no
                                if move.sale_line_id.qty_to_invoice != move_line.qty_done:
                                    vals['quantity'] =  -abs(move_line.qty_done) if move_line.product_id.uom_id.id == move_line.product_id.uom_po_id.id else  -abs(move_line.qty_done / move.sale_line_id.product_uom.factor_inv)
                                invoice_line_list.append((0, 0, vals))
                else:
                    for move in picking_id.move_ids_without_package:
                        if move.sale_line_id:
                            vals = move.sale_line_id._prepare_invoice_line()
                            vals['position_no'] = move.position_no
                            if move.sale_line_id.qty_to_invoice != move.quantity_done:
                                vals['quantity'] =  -abs(move.quantity_done) if move.product_id.uom_id.id == move.product_id.uom_po_id.id else  -abs(move.quantity_done / move.sale_line_id.product_uom.factor_inv)
                            invoice_line_list.append((0, 0, vals))
                
                invoice = picking_id.sale_id._prepare_invoice()
                invoice['picking_id'] = picking_id.id
                invoice['customer_po_no'] = picking_id.customer_po_no
                invoice['do_name'] = picking_id.name
                # invoice['type'] = 'out_refund'
                invoice['invoice_line_ids'] = invoice_line_list
                invoices = self.env['account.move'].create(invoice)
                invoices.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
                picking_id.invoice_created = True
                return invoices

    # def create_vendor_credit(self):
    #     """This is the function for creating refund
    #             from the picking"""
    #     for picking_id in self:
    #         current_user = self.env.uid
    #         if picking_id.picking_type_id.code == 'outgoing':
    #             vendor_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
    #                 'stock_move_invoice.vendor_journal_id') or False
    #             if not vendor_journal_id:
    #                 raise UserError(_("Please configure the journal from the settings."))
    #             invoice_line_list = []
    #             for move_ids_without_package in picking_id.move_ids_without_package:
    #                 vals = (0, 0, {
    #                     'name': move_ids_without_package.description_picking,
    #                     'product_id': move_ids_without_package.product_id.id,
    #                     'price_unit': move_ids_without_package.product_id.lst_price,
    #                     'account_id': move_ids_without_package.product_id.property_account_income_id.id if move_ids_without_package.product_id.property_account_income_id
    #                     else move_ids_without_package.product_id.categ_id.property_account_income_categ_id.id,
    #                     'tax_ids': [(6, 0, [picking_id.company_id.account_purchase_tax_id.id])],
    #                     'quantity': move_ids_without_package.quantity_done,
    #                 })
    #                 invoice_line_list.append(vals)
    #             invoice = picking_id.env['account.move'].create({
    #                 'type': 'in_refund',
    #                 'invoice_origin': picking_id.name,
    #                 'invoice_user_id': current_user,
    #                 # 'narration': picking_id.name,
    #                 'partner_id': picking_id.partner_id.id,
    #                 'currency_id': picking_id.env.user.company_id.currency_id.id,
    #                 'journal_id': int(vendor_journal_id),
    #                 'invoice_payment_ref': picking_id.name,
    #                 'picking_id': picking_id.id,
    #                 'invoice_line_ids': invoice_line_list
    #             })
    #             picking_id.invoice_created = True
    #             return invoice

    def action_open_picking_invoice(self):
        """This is the function of the smart button which redirect to the
        invoice related to the current picking"""
        ac_move = self.env['account.move'].search([('picking_id', '=', self.id)], limit=1)
        if ac_move:
            return {
                'name': 'Invoices',
                'type': 'ir.actions.act_window',
                'view_mode': 'form,tree',
                'res_model': 'account.move',
                'domain': [('picking_id', '=', self.id)],
                # 'context': {'create': False},
                'res_id': ac_move.id,
                'target': 'current'
            }
        
        
class StockReturnInvoicePicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        """in this function the picking is marked as return"""
        new_picking, pick_type_id = super(StockReturnInvoicePicking, self)._create_returns()
        picking = self.env['stock.picking'].browse(new_picking)
        picking.write({'is_return': True})
        return new_picking, pick_type_id


# pass the purchase journal for create a bill

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_create_invoice(self):
        # Call the base method first to create the invoices
        invoices = super(PurchaseOrder, self).action_create_invoice()

        # Update the journal_id for created invoices
        for order in self:
            # Get the journals
            purchase_journal = self.env['account.journal'].search([
                ('type', '=', 'purchase'),
                ('name', '=', 'Purchase (USD)'),
                ('currency_id.name', '=', 'USD'),
                ('company_id', '=', order.company_id.id)
            ], limit=1)

            sales_journal = self.env['account.journal'].search([
                ('type', '=', 'sales'),
                ('name', '=', 'Sales'),
                ('company_id', '=', order.company_id.id)
            ], limit=1)

            print('Purchase Journal:', purchase_journal)
            print('Sales Journal:', sales_journal)

            # Update journal_id if the invoice's journal is of type 'sales'
            for move in order.invoice_ids.filtered(lambda m: m.state == 'draft'):
                if move.journal_id.type == 'sales':
                    move.journal_id = purchase_journal

        return invoices
