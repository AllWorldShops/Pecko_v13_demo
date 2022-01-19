# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.tools.misc import format_date
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):   
    _inherit = "sale.order"
    
    attn = fields.Many2one('res.partner',string="ATTN")
    customer_po_no = fields.Char(string="Customer PO No")
    origin = fields.Char(string='Order Ref No', help="Reference of the document that generated this sales order request.")
    effective_date = fields.Date("Effective Date", compute='_compute_effective_date', store=True, help="Completion date of the first delivery order.")
     
#     @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            for picking in rec.picking_ids:
                picking.write({'attn': self.attn.id,
                                'customer_po_no' :self.customer_po_no})
        for loop in rec.picking_ids:
            for move in loop.move_ids_without_package:
                move.customer_part_no = move.product_id.name
        return res
    
#     @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['attn'] = self.attn.id
        invoice_vals['customer_po_no'] = self.customer_po_no
        return invoice_vals
    
class SaleOrderLine(models.Model):   
    _inherit = "sale.order.line"
    
    customer_part_no = fields.Text(string='Customer Part No')
    need_date = fields.Date(string="Need Date")
    line_no = fields.Integer(string='Position' ,default=False)
    requested_date_line = fields.Date(string="Requested Date")
    order_ref = fields.Char('Order Reference',related='order_id.name')   
    customer_id = fields.Many2one('res.partner',related='order_id.partner_id')
    sales_person_id = fields.Many2one('res.users',related='order_id.user_id')
    promise_date = fields.Datetime('Promised Date',related='order_id.commitment_date')
    promised_date = fields.Date(string="Promised Date")
    customer_po_no = fields.Char('Customer Po No',related='order_id.customer_po_no')   
    internal_ref_no = fields.Char('Internal Ref No',related='product_id.default_code') 
    back_order_qty = fields.Integer(string='Back Order Qty', compute='_compute_back_order_qty', store=True)
    production_type = fields.Selection([('purchase','Purchased'),('manufacture', 'Manufactured')], string="Purchased / Manufactured")
  
#     @api.depends('sequence', 'order_id')
#     def _compute_get_number(self):
#         for recs in self:
#             for order in recs.mapped('order_id'):
#                 line_no_val = 1
#                 for line in order.order_line:
#                     line.line_no = line_no_val
#                     line_no_val += 1

    
    @api.depends('product_uom_qty','qty_delivered')
    def _compute_back_order_qty(self):
        for pro in self:
            if pro.qty_delivered:
                pro.back_order_qty = pro.product_uom_qty - pro.qty_delivered
            else:
                pro.back_order_qty = 0
                
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id.name:
            self.update({'customer_part_no':self.product_id.name,
                         'name':self.product_id.name})
            
            
class AccountGeneralLedgerReport(models.AbstractModel):
    _inherit = "account.general.ledger"
    
    @api.model
    def _get_account_total_line(self, options, account, amount_currency, debit, credit, balance):
        return {
            'id': 'total_%s' % account.id,
            'class': 'o_account_reports_domain_total',
            'parent_id': 'account_%s' % account.id,
            'name': _('Total'),
            'columns': [
                {'name': '', 'class': 'number'},
                {'name': self.format_value(debit), 'class': 'number'},
                {'name': self.format_value(credit), 'class': 'number'},
                {'name': self.format_value(balance), 'class': 'number'},
            ],
            'colspan': 4,
        }

# class AcmoveLine(models.Model):
#     _inherit = "account.move.line"

#     name = fields.Char(string='Label')


class AcAgedinherit(models.AbstractModel):
    _inherit = 'account.aged.partner'

    # def _get_columns_name(self, options):
    #     columns = [
    #         {},
    #         {'name': _("Due Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
    #         {'name': _("Journal"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
    #         {'name': _("Account"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
    #         {'name': _("Exp. Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
            
    #         {'name': _("As of: %s") % format_date(self.env, options['date']['date_to']), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         {'name': _("As of: %s") % format_date(self.env, options['date']['date_to']), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         # {'name': _("1 - Test"), 'class': 'number sortable', '': 'white-space:nowrap;'},
    #         {'name': _("1 - 30"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         {'name': _("1 - 30"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},

    #         {'name': _("31 - 60"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         {'name': _("31 - 60"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},

    #         {'name': _("61 - 90"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         {'name': _("61 - 90"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            
    #         {'name': _("91 - 120"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         {'name': _("91 - 120"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            
    #         {'name': _("Older"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         {'name': _("Older"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            
    #         {'name': _("Total"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         {'name': _("Total"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            
    #         #without cob=nversions
    #         # {'name': _("Due Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
    #         # {'name': _("Journal"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
    #         # {'name': _("Account"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
    #         # {'name': _("Exp. Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
    #         # {'name': _("As of: %s") % format_date(self.env, options['date']['date_to']), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         # {'name': _("1 - 30"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         # {'name': _("31 - 60"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         # {'name': _("61 - 90"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         # {'name': _("91 - 120"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         # {'name': _("Older"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #         # {'name': _("Total"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
    #     ]
    #     return columns

    # @api.model
    # def _get_lines(self, options, line_id=None):
    #     sign = -1.0 if self.env.context.get('aged_balance') else 1.0
    #     lines = []
    #     account_types = [self.env.context.get('account_type')]
    #     context = {'include_nullified_amount': True}
    #     if line_id and 'partner_' in line_id:
    #         # we only want to fetch data about this partner because we are expanding a line
    #         context.update(partner_ids=self.env['res.partner'].browse(int(line_id.split('_')[1])))
    #     results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(**context)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)
        
    #     for values in results:
    #         user_company = self.env.company
    #         user_currency = user_company.currency_id
    #         ac_move = self.env['account.move'].search([('partner_id','=',values['partner_id'])],limit=1)
    #         if ac_move:
                
    #             val_one = round(values['direction'] * ac_move.currency_id.rate, 2)
    #             val_two = round(values['4'] * ac_move.currency_id.rate, 2)
    #             val_three = round(values['3'] * ac_move.currency_id.rate, 2)
    #             val_four = round(values['2'] * ac_move.currency_id.rate, 2)
    #             val_five = round(values['1'] * ac_move.currency_id.rate, 2)
    #             val_six = round(values['0'] * ac_move.currency_id.rate, 2)
    #             val_seven = round(values['total'] * ac_move.currency_id.rate, 2)
    #             cur_one = ac_move.currency_id
    #             # str(country) + '/' + str(process_code)
    #             # print(str(cur_one.symbol) + '' + str(val_one),"///////ccccccccc//////////")
                
    #             if cur_one.position == 'before':
    #                 val_one = str(cur_one.symbol) + ' ' + str(val_one)
    #                 val_two = str(cur_one.symbol) + ' ' + str(val_two)
    #                 val_three = str(cur_one.symbol) + ' ' + str(val_three)
    #                 val_four = str(cur_one.symbol) + ' ' + str(val_four)
    #                 val_five = str(cur_one.symbol) + ' ' + str(val_five)
    #                 val_six = str(cur_one.symbol) + ' ' + str(val_six)
    #                 val_seven = str(cur_one.symbol) + ' ' + str(val_seven)
                    
    #             if cur_one.position == 'after':
    #                 val_one = str(val_one) + ' ' + str(cur_one.symbol)
    #                 val_two = str(val_two) + ' ' + str(cur_one.symbol)
    #                 val_three = str(val_three) + ' ' + str(cur_one.symbol)
    #                 val_four = str(val_four) + ' ' + str(cur_one.symbol)
    #                 val_five = str(val_five) + ' ' + str(cur_one.symbol)
    #                 val_six = str(val_six) + ' ' + str(cur_one.symbol)
    #                 val_seven = str(val_seven) + ' ' + str(cur_one.symbol)

    #             if user_currency.position == 'before':
    #                 values['direction'] = str(user_currency.symbol) + ' ' + str(round(values['direction'],2))
    #                 values['4'] = str(user_currency.symbol) + ' ' + str(round(values['4'],2))
    #                 values['3'] = str(user_currency.symbol) + ' ' + str(round(values['3'],2))
    #                 values['2'] = str(user_currency.symbol) + ' ' + str(round(values['2'],2))
    #                 values['1'] = str(user_currency.symbol) + ' ' + str(round(values['1'],2))
    #                 values['0'] = str(user_currency.symbol) + ' ' + str(round(values['0'],2))
    #                 values['total'] = str(user_currency.symbol) + ' ' + str(round(values['total'],2))

    #             if user_currency.position == 'after':
    #                 values['direction'] = str(round(values['direction'],2)) + ' ' + user_currency.symbol
    #                 values['4'] = str(round(values['4'],2)) + ' ' + user_currency.symbol
    #                 values['3'] = str(round(values['3'],2)) + ' ' + user_currency.symbol
    #                 values['2'] = str(round(values['2'],2)) + ' ' + user_currency.symbol
    #                 values['1'] = str(round(values['1'],2)) + ' ' + user_currency.symbol
    #                 values['0'] = str(round(values['0'],2)) + ' ' + user_currency.symbol
    #                 values['total'] = str(round(values['total'],2)) + ' ' + user_currency.symbol
                
                
    #             vals = {
    #                 'id': 'partner_%s' % (values['partner_id'],),
    #                 'name': values['name'],
    #                 'level': 2,
    #                 'columns': [{'name': ''}] * 4 + [{'name': v}
    #                                                 for v in [values['direction'],val_one, values['4'],val_two,
    #                                                         values['3'],val_three, values['2'],val_four,
    #                                                         values['1'],val_five, values['0'],val_six, values['total'],val_seven]],
    #                 'trust': values['trust'],
    #                 'unfoldable': True,
    #                 'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
    #                 'partner_id': values['partner_id'],
    #             }
    #             lines.append(vals)
    #         if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
    #             for line in amls[values['partner_id']]:
    #                 aml = line['line']
    #                 if aml.move_id.is_purchase_document():
    #                     caret_type = 'account.invoice.in'
    #                 elif aml.move_id.is_sale_document():
    #                     caret_type = 'account.invoice.out'
    #                 elif aml.payment_id:
    #                     caret_type = 'account.payment'
    #                 else:
    #                     caret_type = 'account.move'

    #                 line_date = aml.date_maturity or aml.date
    #                 if not self._context.get('no_format'):
    #                     line_date = format_date(self.env, line_date)
    #                 vals = {
    #                     'id': aml.id,
    #                     'name': aml.move_id.name,
    #                     'class': 'date',
    #                     'caret_options': caret_type,
    #                     'level': 4,
    #                     'parent_id': 'partner_%s' % (values['partner_id'],),
    #                     'columns': [{'name': v} for v in [format_date(self.env, aml.date_maturity or aml.date), aml.journal_id.code, aml.account_id.display_name, format_date(self.env, aml.expected_pay_date)]] +
    #                                [{'name': self.format_value(sign * v, blank_if_zero=True), 'no_format': sign * v} for v in [line['period'] == 7-i and line['amount'] or 0 for i in range(8)]],
    #                     'action_context': {
    #                         'default_type': aml.move_id.type,
    #                         'default_journal_id': aml.move_id.journal_id.id,
    #                     },
    #                     'title_hover': self._format_aml_name(aml.name, aml.ref, aml.move_id.name),
    #                 }
    #                 lines.append(vals)
    #     if total and not line_id:
    #         total_line = {
    #             'id': 0,
    #             'name': _('Total'),
    #             'class': 'total',
    #             'level': 4,
    #             'columns': [{'name': ''}] * 4 + [{'name': self.format_value(sign * v), 'no_format': sign * v} for v in [total[6],0, total[4],0, total[3],0, total[2],0, total[1],0, total[0],0, total[5],0]],
    #         }
    #         lines.append(total_line)
    #     return lines

    


            
        
