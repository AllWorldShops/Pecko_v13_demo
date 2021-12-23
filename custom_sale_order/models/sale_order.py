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
    promise_date = fields.Datetime('Delivery Date',related='order_id.commitment_date')
    promised_date = fields.Date(string="Promised Date")
    customer_po_no = fields.Char('Customer Po No',related='order_id.customer_po_no')   
    internal_ref_no = fields.Char('Internal Ref No',related='product_id.default_code') 
    back_order_qty = fields.Integer(string='Back Order Qty', compute='_compute_back_order_qty', store=True)
  

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
    

class ReportAgedPartnerBalanceInherit(models.AbstractModel):

    _inherit = 'report.account.report_agedpartnerbalance'

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length):
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        # In case of a period_length of 30 days as of 2019-02-08, we want the following periods:
        # Name       Stop         Start
        # 1 - 30   : 2019-02-07 - 2019-01-09
        # 31 - 60  : 2019-01-08 - 2018-12-10
        # 61 - 90  : 2018-12-09 - 2018-11-10
        # 91 - 120 : 2018-11-09 - 2018-10-11
        # +120     : 2018-10-10
        ctx = self._context
        periods = {}
        date_from = fields.Date.from_string(date_from)
        start = date_from
        for i in range(6)[::-1]:
            stop = start - relativedelta(days=period_length)
            period_name = str((6-(i+1)) * period_length + 1) + '-' + str((6-i) * period_length)
            period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
            if i == 0:
                period_name = '+' + str(4 * period_length)
            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop

        res = []
        total = []
        partner_clause = ''
        cr = self.env.cr
        user_company = self.env.company
        user_currency = user_company.currency_id
        company_ids = self._context.get('company_ids') or [user_company.id]
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type), date_from,)
        if 'partner_ids' in ctx:
            if ctx['partner_ids']:
                partner_clause = 'AND (l.partner_id IN %s)'
                arg_list += (tuple(ctx['partner_ids'].ids),)
            else:
                partner_clause = 'AND l.partner_id IS NULL'
        if ctx.get('partner_categories'):
            partner_clause += 'AND (l.partner_id IN %s)'
            partner_ids = self.env['res.partner'].search([('category_id', 'in', ctx['partner_categories'].ids)]).ids
            arg_list += (tuple(partner_ids or [0]),)
        arg_list += (date_from, tuple(company_ids))

        query = '''
            SELECT DISTINCT l.partner_id, res_partner.name AS name, UPPER(res_partner.name) AS UPNAME, CASE WHEN prop.value_text IS NULL THEN 'normal' ELSE prop.value_text END AS trust
            FROM account_move_line AS l
              LEFT JOIN res_partner ON l.partner_id = res_partner.id
              LEFT JOIN ir_property prop ON (prop.res_id = 'res.partner,'||res_partner.id AND prop.name='trust' AND prop.company_id=%s),
              account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND (
                        l.reconciled IS NOT TRUE
                        OR EXISTS (
                            SELECT id FROM account_partial_reconcile where max_date > %s
                            AND (credit_move_id = l.id OR debit_move_id = l.id)
                        )
                    )
                    ''' + partner_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s
            ORDER BY UPPER(res_partner.name)
            '''
        arg_list = (self.env.company.id,) + arg_list
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(8):
            total.append(0)
            print(i,"777777777777777")


        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners]
        lines = dict((partner['partner_id'], []) for partner in partners)
        if not partner_ids:
            return [], [], {}

        lines[False] = []
        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(6):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s
                    ORDER BY COALESCE(l.date_maturity, l.date)'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = [x[0] for x in cr.fetchall()]
            # prefetch the fields that will be used; this avoid cache misses,
            # which look up the cache to determine the records to read, and has
            # quadratic complexity when the number of records is large...
            move_lines = self.env['account.move.line'].browse(aml_ids)
            move_lines._read(['partner_id', 'company_id', 'balance', 'matched_debit_ids', 'matched_credit_ids'])
            move_lines.matched_debit_ids._read(['max_date', 'company_id', 'amount'])
            move_lines.matched_credit_ids._read(['max_date', 'company_id', 'amount'])
            for line in move_lines:
                val = {}
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from, round = False)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from, round = False)
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from, round = False)

                line_amount = user_currency.round(line_amount)
                move_amt = line.move_id.amount_residual
                val['test'] = move_amt
                if not self.env.company.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines.setdefault(partner_id, [])
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                        })
            history.append(partners_amount)

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        test_amt = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) >= %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND l.company_id IN %s
                ORDER BY COALESCE(l.date_maturity, l.date)'''
        cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from, round = False)
            if user_currency.is_zero(line_amount):
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from, round = False)
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from, round = False)
            line_amount = user_currency.round(line_amount)
            move_amt = line.move_id.currency_id.rate
            if not self.env.company.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                print(line_amount * move_amt,"lllllline_amountline_amountline_amountpppppp")
                lines.setdefault(partner_id, [])
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })
                # test_amt[partner_id] += line_amount * move_amt
                print(undue_amounts,"[[[[[[test_amttest_amt]]]]]")


        for partner in partners:
            
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            move_amt = [lines.move_id.amount_total for lines in move_lines]
            print(move_amt,"+++++++++++++++++++ = line.move_id.amount_residual--------")

            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]
            # if partner['partner_id'] in undue_amounts:
                # test_amount = test_amt[partner['partner_id']]
            total[7] = total[7] + undue_amt
            # total[6] = total[6] + test_amount
            values['direction'] = undue_amt
            # values['test'] = test_amount
            if not float_is_zero(values['direction'], precision_rounding=self.env.company.currency_id.rounding):
                at_least_one_amount = True

            for i in range(6):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.company.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(6)])
            # Add for total
            total[(i + 1)] += values['total']
            print(values['total'],"+++++++++++++++++++++++")
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                name = partner['name'] or ''
                values['name'] = len(name) >= 45 and not self.env.context.get('no_format') and name[0:41] + '...' or name
                values['trust'] = partner['trust']
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False

            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)
        return res, total, lines
