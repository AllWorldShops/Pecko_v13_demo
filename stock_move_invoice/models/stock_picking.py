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
from odoo import fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    invoice_count = fields.Integer(string='Invoices', compute='_compute_invoice_count')
    operation_code = fields.Selection(related='picking_type_id.code')
    is_return = fields.Boolean()
    invoice_created = fields.Boolean()
    invoice_status = fields.Selection(related='sale_id.invoice_status', string='Invoice Status', store=True, readonly=True)

    def action_done(self):
        res = super(StockPicking, self).action_done()
        for picking_id in self:
            print(picking_id.state, "picking_id.state")
            if picking_id.state == 'done' and picking_id.picking_type_id.code == 'outgoing' and 'Return' not in str(picking_id.origin):
                print("ssssss")
                picking_id.create_invoice()
            if picking_id.state == 'done' and picking_id.picking_type_id.code == 'incoming' and 'Return' in str(picking_id.origin):
                print("rrrrrrr")
                picking_id.create_customer_credit()
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
            current_user = self.env.uid
            if picking_id.picking_type_id.code == 'outgoing' and picking_id.sale_id:
                # customer_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
                #     'stock_move_invoice.customer_journal_id') or False
                # if not customer_journal_id:
                #     raise UserError(_("Please configure the journal from settings"))
                invoice_line_list = []
                if picking_id.move_line_ids_without_package:
                    for move_line in picking_id.move_line_ids_without_package:
                        if move_line.move_id.sale_line_id:
                            for move in move_line.move_id:
                                vals = move.sale_line_id._prepare_invoice_line()
                                vals['position_no'] = move.position_no
                                invoice_line_list.append((0, 0, vals))
                else:
                    for move in picking_id.move_ids_without_package:
                        if move.sale_line_id:
                            vals = move.sale_line_id._prepare_invoice_line()
                            vals['position_no'] = move.position_no
                            invoice_line_list.append((0, 0, vals))
                if invoice_line_list:
                    invoice = picking_id.sale_id._prepare_invoice()
                    invoice['picking_id'] = picking_id.id
                    invoice['customer_po_no'] = picking_id.customer_po_no
                    invoice['do_name'] = picking_id.name
                    # invoice['invoice_origin'] = picking_id.sale_id.name,
                    invoice['invoice_line_ids'] = invoice_line_list
                    invoices = self.env['account.move'].create(invoice)
                    picking_id.invoice_created = True
                    return invoices

    def create_bill(self):
        """This is the function for creating vendor bill
                from the picking"""
        for picking_id in self:
            current_user = self.env.uid
            if picking_id.picking_type_id.code == 'incoming':
                vendor_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
                    'stock_move_invoice.vendor_journal_id') or False
                if not vendor_journal_id:
                    raise UserError(_("Please configure the journal from the settings."))
                invoice_line_list = []
                for move_ids_without_package in picking_id.move_ids_without_package:
                    vals = (0, 0, {
                        'name': move_ids_without_package.description_picking,
                        'product_id': move_ids_without_package.product_id.id,
                        'price_unit': move_ids_without_package.product_id.lst_price,
                        'account_id': move_ids_without_package.product_id.property_account_income_id.id if move_ids_without_package.product_id.property_account_income_id
                        else move_ids_without_package.product_id.categ_id.property_account_income_categ_id.id,
                        'tax_ids': [(6, 0, [picking_id.company_id.account_purchase_tax_id.id])],
                        'quantity': move_ids_without_package.quantity_done,
                    })
                    invoice_line_list.append(vals)
                invoice = picking_id.env['account.move'].create({
                    'type': 'in_invoice',
                    'invoice_origin': picking_id.name,
                    'invoice_user_id': current_user,
                    # 'narration': picking_id.name,
                    'partner_id': picking_id.partner_id.id,
                    'currency_id': picking_id.env.user.company_id.currency_id.id,
                    'journal_id': int(vendor_journal_id),
                    'invoice_payment_ref': picking_id.name,
                    'picking_id': picking_id.id,
                    'invoice_line_ids': invoice_line_list
                })
                picking_id.invoice_created = True
                return invoice

    def create_customer_credit(self):
        """This is the function for creating customer credit note
                from the picking"""
        for picking_id in self:
            current_user = picking_id.env.uid
            if picking_id.picking_type_id.code == 'incoming' and picking_id.sale_id:
                # customer_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
                #     'stock_move_invoice.customer_journal_id') or False
                # if not customer_journal_id:
                #     raise UserError(_("Please configure the journal from settings"))
                invoice_line_list = []
                if picking_id.move_line_ids_without_package:
                    for move_line in picking_id.move_line_ids_without_package:
                        if move_line.move_id.sale_line_id:
                            for move in move_line.move_id:
                                vals = move.sale_line_id._prepare_invoice_line()
                                vals['position_no'] = move.position_no
                                invoice_line_list.append((0, 0, vals))
                else:
                    for move in picking_id.move_ids_without_package:
                        if move.sale_line_id:
                            vals = move.sale_line_id._prepare_invoice_line()
                            vals['position_no'] = move.position_no
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

    def create_vendor_credit(self):
        """This is the function for creating refund
                from the picking"""
        for picking_id in self:
            current_user = self.env.uid
            if picking_id.picking_type_id.code == 'outgoing':
                vendor_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
                    'stock_move_invoice.vendor_journal_id') or False
                if not vendor_journal_id:
                    raise UserError(_("Please configure the journal from the settings."))
                invoice_line_list = []
                for move_ids_without_package in picking_id.move_ids_without_package:
                    vals = (0, 0, {
                        'name': move_ids_without_package.description_picking,
                        'product_id': move_ids_without_package.product_id.id,
                        'price_unit': move_ids_without_package.product_id.lst_price,
                        'account_id': move_ids_without_package.product_id.property_account_income_id.id if move_ids_without_package.product_id.property_account_income_id
                        else move_ids_without_package.product_id.categ_id.property_account_income_categ_id.id,
                        'tax_ids': [(6, 0, [picking_id.company_id.account_purchase_tax_id.id])],
                        'quantity': move_ids_without_package.quantity_done,
                    })
                    invoice_line_list.append(vals)
                invoice = picking_id.env['account.move'].create({
                    'type': 'in_refund',
                    'invoice_origin': picking_id.name,
                    'invoice_user_id': current_user,
                    # 'narration': picking_id.name,
                    'partner_id': picking_id.partner_id.id,
                    'currency_id': picking_id.env.user.company_id.currency_id.id,
                    'journal_id': int(vendor_journal_id),
                    'invoice_payment_ref': picking_id.name,
                    'picking_id': picking_id.id,
                    'invoice_line_ids': invoice_line_list
                })
                picking_id.invoice_created = True
                return invoice

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

    # def action_open_picking_invoice(self):
    #     invoices = self.invoice_count
    #     action = self.env.ref('account.action_move_out_invoice_type').read()[0]
    #     if invoices > 1:
    #         action['domain'] = [('picking_id', '=', self.id)]
    #     elif invoices == 1:
    #         form_view = [(self.env.ref('account.view_move_form').id, 'form')]
    #         if 'views' in action:
    #             action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
    #         else:
    #             action['views'] = form_view
    #         action['res_id'] = invoices.id
    #     else:
    #         action = {'type': 'ir.actions.act_window_close'}

    #     context = {
    #         'default_type': 'out_invoice',
    #     }
    #     if len(self.sale_id) == 1:
    #         context.update({
    #             'default_partner_id': self.sale_id.partner_id.id,
    #             'default_partner_shipping_id': self.sale_id.partner_shipping_id.id,
    #             'default_invoice_payment_term_id': self.sale_id.payment_term_id.id or self.sale_id.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
    #             'default_invoice_origin': self.sale_id.mapped('name'),
    #             'default_user_id': self.sale_id.user_id.id,
    #         })
    #     action['context'] = context
    #     return action


class StockReturnInvoicePicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        """in this function the picking is marked as return"""
        new_picking, pick_type_id = super(StockReturnInvoicePicking, self)._create_returns()
        picking = self.env['stock.picking'].browse(new_picking)
        picking.write({'is_return': True})
        return new_picking, pick_type_id

