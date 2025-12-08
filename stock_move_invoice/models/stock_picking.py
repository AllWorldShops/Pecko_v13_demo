from odoo import fields, models, api, _
import requests
import json
import logging
_logger = logging.getLogger(__name__)

import ast

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    invoice_count = fields.Integer(string='Invoices', compute='_compute_invoice_count')
    operation_code = fields.Selection(related='picking_type_id.code')
    is_return = fields.Boolean()
    invoice_created = fields.Boolean()
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_status = fields.Selection(related='sale_id.invoice_status', string='Invoice Status', store=True, readonly=True)
    custom_form_reference_number = fields.Char(string='Customs Form Reference Number')
    custom_form_date = fields.Datetime(string='Customs Form Date')

    def action_update_dates(self):
        # Read move name from system parameters
        param_name = self.env['ir.config_parameter'].sudo().get_param('update_move_name')
        print('param_name',param_name)

        actual_list = ast.literal_eval(param_name)

        if not param_name:
            raise UserError("System parameter 'update_move_name' is not set.")
        # print('------------------',list(str(param_name)))
        # stop
        moves = self.env["account.move"].search([("name", "in", actual_list)])
        print('moves',moves)
        
        for move in moves:
            payment = self.env["account.payment"].search([("name", "=", move.name)], limit=1)
            print('payment',payment)
            if not payment:
                continue

            # Update move date
            query = """ UPDATE account_move SET date = %s WHERE id = %s """
            self.env.cr.execute(query, (payment.date, move.id))

            # move.date = payment.date

            # Update move lines
            for line in move.line_ids:
                move_li_query = """ UPDATE account_move_line SET date = %s WHERE id = %s """
                self.env.cr.execute(move_li_query, (payment.date, line.id))
                # line.date = payment.date

                # Fetch partial reconciles
                partials = self.env["account.partial.reconcile"].search([("credit_move_id", "=", line.id)])
                print('partials',partials)
                for partial in partials:
                    if partial.debit_move_id:
                        # Update debit line
                        move_query = """ UPDATE account_move_line SET date = %s WHERE id = %s """
                        self.env.cr.execute(move_query, (payment.date, partial.debit_move_id.id))
                        # partial.debit_move_id.date = payment.date

                        # Update parent move
                        if partial.debit_move_id.move_id:
                            move_line_query = """ UPDATE account_move SET date = %s WHERE id = %s """
                            self.env.cr.execute(move_line_query, (payment.date, partial.debit_move_id.move_id.id))
                            # partial.debit_move_id.move_id.date = payment.date
                if partials:
                    print('partial.full_reconcile_id',partials[0].full_reconcile_id)
                    if partials[0].full_reconcile_id:
                        full_move_query = """ UPDATE account_move_line SET date = %s WHERE full_reconcile_id = %s """
                        self.env.cr.execute(full_move_query, (payment.date, partials[0].full_reconcile_id.id))

                        full_partials = self.env["account.move.line"].search([("full_reconcile_id", "=", partials[0].full_reconcile_id.id)])
                        print('full_partials',full_partials)
                        for rec in full_partials:
                            fulls_move_query = """ UPDATE account_move_line SET date = %s WHERE move_id = %s """
                            self.env.cr.execute(fulls_move_query, (payment.date, rec.move_id.id))
                            fullss_move_query = """ UPDATE account_move SET date = %s WHERE id = %s """
                            self.env.cr.execute(fullss_move_query, (payment.date, rec.move_id.id))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Success",
                'message': "Move Dates Updated Successfully",
                'sticky': False,
            }
        }

    @api.onchange('custom_form_reference_number', 'custom_form_date')
    def _onchange_custom_form_fields(self):
        for picking in self:
            if picking.picking_type_id.code in ['incoming', 'outgoing']:
                if picking.invoice_id:
                    if picking.custom_form_reference_number:
                        picking.invoice_id.l10n_my_edi_custom_form_reference = picking.custom_form_reference_number
                    if picking.custom_form_date:
                        picking.invoice_id.custom_form_date = picking.custom_form_date
            if picking.picking_type_id.code == 'incoming':
                invoices = self.env['account.move'].search([('receipts_id', '=', picking.id)])
                for invoice in invoices:
                    invoice_id.l10n_my_edi_custom_form_reference = picking.custom_form_reference_number
                    invoice_id.custom_form_date = picking.custom_form_date


    def write(self, vals):
        res = super().write(vals)
        if 'custom_form_reference_number' in vals or 'custom_form_date' in vals:
            for picking in self:
                invoices = self.env['account.move'].search(['|',('picking_id', '=', picking.id),('receipts_id','=',picking.id)])
                for invoice in invoices:
                    if 'custom_form_reference_number' in vals:
                        invoice.l10n_my_edi_custom_form_reference = vals['custom_form_reference_number']
                    if 'custom_form_date' in vals:
                        invoice.custom_form_date = vals['custom_form_date']
        return res


    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking_id in self:
            if picking_id.state == 'done' and picking_id.picking_type_id.code == 'outgoing' and picking_id.sale_id:
                picking_id.create_invoice()
            print('picking_id.state',picking_id.state)
            print('picking_id.picking_type_id.code',picking_id.picking_type_id.code)
            print('picking_id.sale_id',picking_id.sale_id)

            if picking_id.state == 'done' and picking_id.picking_type_id.code == 'incoming' and picking_id.sale_id:
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
                            'quantity': str(line.quantity),
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
            print('picking_id.invoice_status',picking_id.invoice_status)
            
            if picking_id.invoice_status not in ['invoiced', 'no']:
                journal_id = False
                journal_id = self.env['account.journal'].search([('type','=','sale'),('company_id','=',picking_id.company_id.id),('name','=', 'Sales')],limit=1).id
                print('journal_id',journal_id)
                invoice_line_list = []
                if picking_id.move_line_ids_without_package:
                    for move_line in picking_id.move_line_ids_without_package:
                        if move_line.move_id.sale_line_id:
                            for move in move_line.move_id:
                                vals = move.sale_line_id._prepare_invoice_line()
                                vals['position_no'] = move.position_no
                                if move.sale_line_id.qty_to_invoice != move_line.quantity:
                                    vals['quantity'] = move_line.quantity if move_line.product_id.uom_id.id == move_line.product_id.uom_po_id.id else move_line.quantity / move.sale_line_id.product_uom.factor_inv
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
                    invoice['l10n_my_edi_custom_form_reference'] = picking_id.custom_form_reference_number
                    # invoice['invoice_origin'] = picking_id.sale_id.name,
                    invoice['invoice_line_ids'] = invoice_line_list
                    invoices = self.env['account.move'].create(invoice)
                    picking_id.invoice_created = True
                    picking_id.invoice_id = invoices.id
                    print('--------------',invoice['journal_id'])
                    
                    return invoices

    def create_customer_credit(self):

        """This is the function for creating customer credit note
                from the picking"""
        for picking_id in self:
            print('picking_id.invoice_status',picking_id.invoice_status)
            if picking_id.invoice_status in ['to invoice','invoiced']:
                invoice_line_list = []
                if picking_id.move_line_ids_without_package:
                    for move_line in picking_id.move_line_ids_without_package:
                        if move_line.move_id.sale_line_id:
                            for move in move_line.move_id:
                                vals = move.sale_line_id._prepare_invoice_line()
                                vals['position_no'] = move.position_no
                                if move.sale_line_id.qty_to_invoice != move_line.quantity:
                                    vals['quantity'] = abs(move_line.quantity) if move_line.product_id.uom_id.id == move_line.product_id.uom_po_id.id else abs(move_line.quantity / move.sale_line_id.product_uom.factor_inv)
                                invoice_line_list.append((0, 0, vals))
                else:
                    for move in picking_id.move_ids_without_package:
                        if move.sale_line_id:
                            vals = move.sale_line_id._prepare_invoice_line()
                            vals['position_no'] = move.position_no
                            if move.sale_line_id.qty_to_invoice != move.quantity_done:
                                vals['quantity'] = abs(move.quantity_done) if move.product_id.uom_id.id == move.product_id.uom_po_id.id else abs(move.quantity_done / move.sale_line_id.product_uom.factor_inv)
                            invoice_line_list.append((0, 0, vals))
                
                invoice = picking_id.sale_id._prepare_invoice()
                invoice['picking_id'] = picking_id.id
                invoice['customer_po_no'] = picking_id.customer_po_no
                invoice['do_name'] = picking_id.name
                invoice['move_type'] = 'out_refund'
                invoice['invoice_line_ids'] = invoice_line_list
                invoices = self.env['account.move'].create(invoice)
                # invoices.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
                picking_id.invoice_created = True
                return invoices

    def action_open_picking_invoice(self):
        """This is the function of the smart button which redirect to the
        invoice related to the current picking"""
        ac_move = self.env['account.move'].search([('picking_id', '=', self.id)], limit=1)
        if ac_move:
            return {
                'name': 'Invoices',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.move',
                'domain': [('picking_id', '=', self.id)],
                'res_id': ac_move.id,
                'target': 'current'
            }
        
        
class StockReturnInvoicePicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.model
    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
        
        return {
            'product_id': stock_move.product_id.id,
            'quantity': stock_move.quantity,
            'move_id': stock_move.id,
            'uom_id': stock_move.product_id.uom_id.id,
        }
    
    def _create_returns(self):
        """in this function the picking is marked as return"""
        new_picking, pick_type_id = super(StockReturnInvoicePicking, self)._create_returns()
        picking = self.env['stock.picking'].browse(new_picking)
        picking.write({'is_return': True})
        return new_picking, pick_type_id

