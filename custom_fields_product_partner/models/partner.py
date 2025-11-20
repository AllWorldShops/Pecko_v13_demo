from odoo import models, fields
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools.translate import _
from odoo import api, fields, models, Command, _


class Partner(models.Model):
    _inherit = 'res.partner'

    activity_date_deadline = fields.Datetime(string='Activity')
    message_last_post = fields.Datetime(string='Message')
    commercial_partner_country_id = fields.Many2one('res.country', related='commercial_partner_id.country_id')
    opt_out = fields.Boolean('Opt Out',
                             help="If opt-out is checked, this contact has refused to receive emails for mass mailing and marketing campaign." "Filter 'Available for Mass Mailing' allows users to filter the partners when performing mass mailing.")
    has_address = fields.Boolean(string='Is address valid', readonly=True, store=True)
    x_studio_field_cH3lX = fields.Char(string='type')
    x_studio_field_cpiWw = fields.Char('Supplier Name')
    x_studio_field_MTmaF = fields.Selection([('PEI', 'PEI'), ('PKS', 'PKS'), ('PM', 'PM'), ('Avill', 'Avill')],
                                            string='Verification Status')
    incoterms = fields.Char("IncoTerm")

class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = "account.move.line"
    _description = "Journal Item"

    customer_po_no = fields.Char(
        related='move_id.customer_po_no', store=True, copy=False,
    )

    def _prepare_exchange_difference_move_vals(self, amounts_list, company=None, exchange_date=None, **kwargs):
        """ Prepare values to create later the exchange difference journal entry.
        The exchange difference journal entry is there to fix the debit/credit of lines when the journal items are
        fully reconciled in foreign currency.
        :param amounts_list:    A list of dict, one for each aml.
        :param company:         The company in case there is no aml in self.
        :param exchange_date:   Optional date object providing the date to consider for the exchange difference.
        :return:                A python dictionary containing:
            * move_vals:    A dictionary to be passed to the account.move.create method.
            * to_reconcile: A list of tuple <move_line, sequence> in order to perform the reconciliation after the move
                            creation.
        """
        company = (
            (self.move_id.filtered(lambda m: m.is_invoice(True)) or self.move_id).company_id
            or company
        )[:1]
        if not company:
            return

        journal = self._get_exchange_journal(company)

        accounting_exchange_date = journal.with_context(move_date=exchange_date).accounting_date if journal else date.min
        
        # Forex date mismatched correction starts
        accounting_exchange_date = exchange_date
        # Forex date mismatched correction ends

        move_vals = {
            'move_type': 'entry',
            'name': '/', # do not trigger the compute name before posting as it will most likely be posted immediately after
            'date': accounting_exchange_date,
            'journal_id': journal.id,
            'line_ids': [],
            'always_tax_exigible': True,
        }
        to_reconcile = []

        for line, amounts in zip(self, amounts_list):
            move_vals['date'] = max(move_vals['date'], line.date)

            if 'amount_residual' in amounts:
                amount_residual = amounts['amount_residual']
                amount_residual_currency = 0.0
                if line.currency_id == line.company_id.currency_id:
                    amount_residual_currency = amount_residual
                amount_residual_to_fix = amount_residual
                if line.company_currency_id.is_zero(amount_residual):
                    continue
            elif 'amount_residual_currency' in amounts:
                amount_residual = 0.0
                amount_residual_currency = amounts['amount_residual_currency']
                amount_residual_to_fix = amount_residual_currency
                if line.currency_id.is_zero(amount_residual_currency):
                    continue
            else:
                continue

            exchange_line_account = self._get_exchange_account(company, amount_residual_to_fix)

            sequence = len(move_vals['line_ids'])
            line_vals = [
                {
                    'name': _('Currency exchange rate difference'),
                    'debit': -amount_residual if amount_residual < 0.0 else 0.0,
                    'credit': amount_residual if amount_residual > 0.0 else 0.0,
                    'amount_currency': -amount_residual_currency,
                    'full_reconcile_id': line.full_reconcile_id.id,
                    'account_id': line.account_id.id,
                    'currency_id': line.currency_id.id,
                    'partner_id': line.partner_id.id,
                    'sequence': sequence,
                },
                {
                    'name': _('Currency exchange rate difference'),
                    'debit': amount_residual if amount_residual > 0.0 else 0.0,
                    'credit': -amount_residual if amount_residual < 0.0 else 0.0,
                    'amount_currency': amount_residual_currency,
                    'account_id': exchange_line_account.id,
                    'currency_id': line.currency_id.id,
                    'partner_id': line.partner_id.id,
                    'sequence': sequence + 1,
                },
            ]

            if kwargs.get('exchange_analytic_distribution'):
                line_vals[1].update({'analytic_distribution': kwargs['exchange_analytic_distribution']})

            move_vals['line_ids'] += [Command.create(vals) for vals in line_vals]
            to_reconcile.append((line, sequence))

        return {'move_values': move_vals, 'to_reconcile': to_reconcile}

class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"

    def _get_columns_name(self, options):
        headers = [{},
                   {'name': _('Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('Due Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('Source Document'), 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('Customer PO No.'), 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('Communication'), 'style': 'text-align:right; white-space:nowrap;'},
                   {'name': _('Expected Date'), 'class': 'date', 'style': 'white-space:nowrap;'},
                   {'name': _('Excluded'), 'class': 'date', 'style': 'white-space:nowrap;'},
                   {'name': _('Total Due'), 'class': 'number o_price_total',
                    'style': 'text-align:right; white-space:nowrap;'},
                   {'name': _('Running Total'), 'class': 'number o_price_total',
                    'style': 'text-align:right; white-space:nowrap;'}
                   ]
        if self.env.context.get('print_mode'):
            headers = headers[:5] + headers[7:]  # Remove the 'Expected Date' and 'Excluded' columns
        return headers

    def _get_lines(self, options, line_id=None):
        # Get date format for the lang
        partner = options.get('partner_id') and self.env['res.partner'].browse(options['partner_id']) or False
        if not partner:
            return []

        lang_code = partner.lang if self._context.get('print_mode') else self.env.user.lang or get_lang(self.env).code
        lines = []
        res = {}
        today = fields.Date.today()
        line_num = 0
        for l in partner.unreconciled_aml_ids.filtered(lambda l: l.company_id == self.env.company):
            if l.company_id == self.env.company:
                if self.env.context.get('print_mode') and l.blocked:
                    continue
                currency = l.currency_id or l.company_id.currency_id
                if currency not in res:
                    res[currency] = []
                res[currency].append(l)
        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            sum_amt = 0
            print("=======", aml_recs)
            aml_obj = self.env['account.move.line']
            for aml_sort in aml_recs:
                aml_obj = aml_obj + aml_sort
            for aml in aml_obj.sorted(key=lambda r: r.date_maturity or r.date, reverse=False):
                amount = aml.amount_residual_currency if aml.currency_id else aml.amount_residual
                sum_amt += amount
                s1 = round(sum_amt, 2)
                s1 = f"{s1:,}"
                cur_aml = aml.move_id.currency_id
                if cur_aml.position == 'before':
                    running_total = str(cur_aml.symbol) + ' ' + s1
                if cur_aml.position == 'after':
                    running_total = s1 + ' ' + str(cur_aml.symbol)
                date_due = format_date(self.env, aml.date_maturity or aml.date, lang_code=lang_code)
                total += not aml.blocked and amount or 0
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                is_payment = aml.payment_id
                if is_overdue or is_payment:
                    total_issued += not aml.blocked and amount or 0
                if is_overdue:
                    date_due = {'name': date_due, 'class': 'color-red date',
                                'style': 'white-space:nowrap;text-align:center;color: red;'}
                if is_payment:
                    date_due = ''
                move_line_name = aml.move_id.name or aml.name
                if self.env.context.get('print_mode'):
                    move_line_name = {'name': move_line_name, 'style': 'text-align:right; white-space:normal;'}
                amount = formatLang(self.env, amount, currency_obj=currency)
                # sum_amt = formatLang(self.env, sum_amt, currency_obj=currency)
                line_num += 1
                expected_pay_date = format_date(self.env, aml.expected_pay_date,
                                                lang_code=lang_code) if aml.expected_pay_date else ''
                columns = [
                    format_date(self.env, aml.date, lang_code=lang_code),
                    date_due,
                    aml.move_id.invoice_origin or '',
                    aml.move_id.customer_po_no or '',
                    move_line_name,
                    (expected_pay_date and expected_pay_date + ' ') + (aml.internal_note or ''),
                    {'name': '', 'blocked': aml.blocked},
                    amount,
                    running_total,
                ]
                if self.env.context.get('print_mode'):
                    columns = columns[:4] + columns[6:]
                lines.append({
                    'id': aml.id,
                    'account_move': aml.move_id,
                    'name': aml.move_id.name,
                    'caret_options': 'followup',
                    'move_id': aml.move_id.id,
                    'type': is_payment and 'payment' or 'unreconciled_aml',
                    'unfoldable': False,
                    'columns': [type(v) == dict and v or {'name': v} for v in columns],
                })
            total_due = formatLang(self.env, total, currency_obj=currency)
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': 'total',
                'style': 'border-top-style: double',
                'unfoldable': False,
                'level': 3,
                'columns': [{'name': v} for v in [''] * (4 if self.env.context.get('print_mode') else 6) + [
                    total >= 0 and _('Total Due') or '', total_due]],
            })
            if total_issued > 0:
                total_issued = formatLang(self.env, total_issued, currency_obj=currency)
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'class': 'total',
                    'unfoldable': False,
                    'level': 3,
                    'columns': [{'name': v} for v in
                                [''] * (4 if self.env.context.get('print_mode') else 6) + [_('Total Overdue'),
                                                                                           total_issued]],
                })
            # Add an empty line after the total to make a space between two currencies
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': '',
                'style': 'border-bottom-style: none',
                'unfoldable': False,
                'level': 0,
                'columns': [{} for col in columns],
            })
        # Remove the last empty line
        if lines:
            lines.pop()
        return lines