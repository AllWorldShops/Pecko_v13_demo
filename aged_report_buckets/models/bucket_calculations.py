from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo import fields, models, api, _
from odoo.tools.misc import format_date
from datetime import datetime


class AgedReceivable(models.AbstractModel):
    _inherit = 'account.aged.partner.balance.report.handler'


    def _get_columns_name(self, options):
        columns = [{}]
        if not self._context.get('days'):
            bucket_days = int(self.env['ir.config_parameter'].sudo().get_param('aged_report_buckets.days_count'))
        else:
            bucket_days = int(self._context['days'])
            self.env['ir.config_parameter'].sudo().set_param('aged_report_buckets.days_count', bucket_days)

        fts = 1
        fte = bucket_days
        ss = fte + 1
        se = bucket_days * 2
        ts = se + 1
        te = bucket_days * 3
        fs = te + 1
        fe = bucket_days * 4
        columns += [
            {'name': v, 'class': 'number', 'style': 'white-space:nowrap;'}
            for v in [_("JRNL"), _("Account"), _("Reference"), _("Not due on: %s") % format_date(self.env, options['date']['date_to']),'Conversion',
                      _(str(fts) + "-" + str(fte) +' Days'),'Conversion', _(str(ss) + "-" + str(se) +' Days'),'Conversion', _(str(ts) + "-" + str(te) +' Days'),'Conversion', _(str(fs) + "-" + str(fe) +' Days'),'Conversion', _("Older"),'Conversion', _("Total"),'Conversion']
        ]
        return columns

    @api.model
    def _get_lines(self, options, line_id=None):
#         print('---------------------',self._context)
#         print('+++++++++++++++++',self._context.get('days'))
        if not self._context.get('days'):
            bucket_days = int(self.env['ir.config_parameter'].sudo().get_param('aged_report_buckets.days_count'))
        else:
#         print('---------------------',self._context['days'])
            bucket_days = int(self._context['days'])
            self.env['ir.config_parameter'].sudo().set_param('aged_report_buckets.days_count', bucket_days)

        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(include_nullified_amount=True)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', bucket_days)
        for values in results:
            user_company = self.env.company
            # print(user_company.name,"////user_companyuser_companyuser_company+=========")
            user_currency = user_company.currency_id
            move = self.env['account.move'].search([('partner_id','=',values['partner_id']),('state','=', 'posted'),('type','=', 'out_invoice')],order='invoice_date desc')
            # for moves in move:
            print(move[:1].partner_id.name, "sss",  move[:1], "invoice_dateinvoice_date---------")
            ac_move = move[:1]
            # if ac_move:
            r1 = round(values['direction'],2)
            r2 = round(values['4'],2)
            r3 = round(values['3'],2)
            r4 = round(values['2'],2)
            r5 = round(values['1'],2)
            r6 = round(values['0'],2)
            r7 = round(values['total'],2)

            v1 = f"{r1:,}"
            v2 = f"{r2:,}"
            v3 = f"{r3:,}"
            v4 = f"{r4:,}"
            v5 = f"{r5:,}"
            v6 = f"{r6:,}"
            v7 = f"{r7:,}"
            # print(v6, "////++++++++=================")
            if ac_move.exchange_rate > 1:
                val_one = round(values['direction'] / ac_move.exchange_rate, 2)
                val_two = round(values['4'] / ac_move.exchange_rate, 2)
                val_three = round(values['3'] / ac_move.exchange_rate, 2)
                val_four = round(values['2'] / ac_move.exchange_rate, 2)
                val_five = round(values['1'] / ac_move.exchange_rate, 2)
                val_six = round(values['0'] / ac_move.exchange_rate, 2)
                val_seven = round(values['total'] / ac_move.exchange_rate, 2)
            else:
                val_one = round(values['direction'] * ac_move.exchange_rate, 2)
                val_two = round(values['4'] * ac_move.exchange_rate, 2)
                val_three = round(values['3'] * ac_move.exchange_rate, 2)
                val_four = round(values['2'] * ac_move.exchange_rate, 2)
                val_five = round(values['1'] * ac_move.exchange_rate, 2)
                val_six = round(values['0'] * ac_move.exchange_rate, 2)
                val_seven = round(values['total'] * ac_move.exchange_rate, 2)

            c1 = f"{val_one:,}"
            c2 = f"{val_two:,}"
            c3 = f"{val_three:,}"
            c4 = f"{val_four:,}"
            c5 = f"{val_five:,}"
            c6 = f"{val_six:,}"
            c7 = f"{val_seven:,}"
            # print(c1, "xxcccc-----------")

            cur_one = ac_move.currency_id
            # print(cur_one.name, "cur_onecur_one============")
            # print(ac_move.invoice_date, "invoice_dateinvoice_date------------")
            if cur_one.position == 'before':
                c1 = str(cur_one.symbol) + ' ' + str(c1)
                c2 = str(cur_one.symbol) + ' ' + str(c2)
                c3 = str(cur_one.symbol) + ' ' + str(c3)
                c4 = str(cur_one.symbol) + ' ' + str(c4)
                c5 = str(cur_one.symbol) + ' ' + str(c5)
                c6 = str(cur_one.symbol) + ' ' + str(c6)
                c7 = str(cur_one.symbol) + ' ' + str(c7)

            if cur_one.position == 'after':
                c1 = str(c1) + ' ' + str(cur_one.symbol)
                c2 = str(c2) + ' ' + str(cur_one.symbol)
                c3 = str(c3) + ' ' + str(cur_one.symbol)
                c4 = str(c4) + ' ' + str(cur_one.symbol)
                c5 = str(c5) + ' ' + str(cur_one.symbol)
                c6 = str(c6) + ' ' + str(cur_one.symbol)
                c7 = str(c7) + ' ' + str(cur_one.symbol)

            if user_currency.position == 'before':
                values['direction'] = str(user_currency.symbol) + ' ' + v1
                values['4'] = str(user_currency.symbol) + ' ' + v2
                values['3'] = str(user_currency.symbol) + ' ' + v3
                values['2'] = str(user_currency.symbol) + ' ' + v4
                values['1'] = str(user_currency.symbol) + ' ' + v5
                values['0'] = str(user_currency.symbol) + ' ' + v6
                values['total'] = str(user_currency.symbol) + ' ' + v7

            if user_currency.position == 'after':
                values['direction'] = v1 + ' ' + user_currency.symbol
                values['4'] = v2 + ' ' + user_currency.symbol
                values['3'] = v3 + ' ' + user_currency.symbol
                values['2'] = v4 + ' ' + user_currency.symbol
                values['1'] = v5 + ' ' + user_currency.symbol
                values['0'] = v6 + ' ' + user_currency.symbol
                values['total'] = v7 + ' ' + user_currency.symbol
            # print(val_one, "val_oneval_oneval_one------")
            if line_id and 'partner_%s' % (values['partner_id'],) != line_id:
                continue
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': values['name'],
                'level': 2,
                'columns': [{'name': ''}] * 3 + [{'name':  v} for v in [values['direction'],c1, values['4'],c2,
                                                                                                 values['3'],c3, values['2'],c4,
                                                                                                 values['1'],c5, values['0'],c6, values['total'],c7]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    caret_type = 'account.move'
                    if aml.move_id:
                        caret_type = 'account.invoice.in' if aml.move_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    fts = 1
                    fte = bucket_days
                    ss = fte + 1
                    se = bucket_days * 2
                    ts = se + 1
                    te = bucket_days * 3
                    fs = te + 1
                    fe = bucket_days * 4
                    date_format = "%Y-%m-%d"
                    date_to = datetime.strptime(str(self._context['date_to']), date_format)
                    rep_date = datetime.strptime(str(aml.date_maturity or aml.date), date_format)
                    delta = date_to - rep_date
                    diff_days = int(delta.days)
                    # print(diff_days, "delta__")
                    a_var = []
                    b_var = []
                    c_var = []
                    d_var = []
                    for i in range(fts, fte):
                        a_var.append(i)
                    for i in range(ss, se):
                        b_var.append(i)
                    for i in range(ts, te):
                        c_var.append(i)
                    for i in range(fs, fe):
                        d_var.append(i)
                    cur_aml = aml.move_id.currency_id
                    if aml.move_id.exchange_rate > 1:
                        inv_total = aml.move_id.amount_total * aml.move_id.exchange_rate
                    else:
                        inv_total = aml.move_id.amount_total / aml.move_id.exchange_rate
                    conv_amt = aml.move_id.amount_total
                    t1 = round(inv_total, 2)
                    s1 = f"{t1:,}"
                    t2 = round(conv_amt, 2)
                    s2 = f"{t2:,}"

                    if cur_aml.position == 'before':
                        conv_amt = str(cur_aml.symbol) + ' ' + s2
                    if cur_aml.position == 'after':
                        conv_amt = s2 + ' ' + str(cur_aml.symbol)
                    if user_currency.position == 'before':
                        inv_total = str(user_currency.symbol) + ' ' + s1
                    if user_currency.position == 'after':
                        inv_total = s1 + ' ' + str(user_currency.symbol)

                    vals = {
                        'id': aml.id,
                        'name': aml.date_maturity or aml.date,
                        'caret_options': caret_type,
                        'class': 'date',
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': v} for v in [aml.journal_id.code, aml.account_id.display_name, aml.move_id.customer_po_no]] +
                                   [{'name': v} for v in [inv_total if diff_days == 0 else False, conv_amt if diff_days == 0 else False,
                                                        inv_total if diff_days in a_var else False, conv_amt if diff_days in a_var else False,
                                                        inv_total if diff_days in b_var else False, conv_amt if diff_days in b_var else False,
                                                        inv_total if diff_days in c_var else False, conv_amt if diff_days in c_var else False,
                                                        inv_total if diff_days in d_var else False, conv_amt if diff_days in d_var else False,
                                                        inv_total if diff_days > d_var[-1] else False, conv_amt if diff_days > d_var[-1] else False]],
                        # 'columns': [{'name': v} for v in [aml.journal_id.code, aml.account_id.display_name, format_date(self.env, aml.expected_pay_date)]] +
                        #            [{'name': self.format_value(sign * v, blank_if_zero=True), 'no_format': sign * v} for v in [line['period'] == 7-i and line['amount'] or 0 for i in range(8)]],
                        'action_context': {
                            'default_type': aml.move_id.type,
                            'default_journal_id': aml.move_id.journal_id.id,
                        },
                        'title_hover': self._format_aml_name(aml.name, aml.ref, aml.move_id.name),
                    }
                    lines.append(vals)

        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 'None',
                'columns': [{'name': ''}] * 3 + [{'name': self.format_value(sign * v)} for v in [total[6],0, total[4],0, total[3],0, total[2],0, total[1],0, total[0],0, total[5],0]],
            }
            lines.append(total_line)
        return lines
#
    
class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    def _get_reports_buttons(self):
        return [{'name': _('Print Preview'), 'action': 'print_pdf'}, {'name': _('Export (XLSX)'), 'action': 'print_xlsx'}, {'name': _('Bucket Days'), 'action': 'bucket_calc'}]

    def bucket_calc(self,options):
        view_id = self.env.ref('aged_report_buckets.bucket_days_wizard').id
        print (view_id)
        return {'type': 'ir.actions.act_window',
                'name': _(''),
                'res_model': 'bucket.days',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'views': [[view_id, 'form']],
        }