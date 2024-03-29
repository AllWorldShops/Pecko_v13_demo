from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import format_date, Query
from odoo.tools import formatLang, Query
# from odoo.tools import name, Query

# from odoo.tools import
#     date_utils,
#     email_re,
#     email_split,
#     float_compare,
#     float_is_zero,
#     float_repr,
#     format_amount,
#     format_date,
#     formatLang,
#     frozendict,
#     get_lang,
#     is_html_empty,
#     sql
# )


class AccountFollowupReport(models.AbstractModel):
    _inherit = 'account.followup.report'
    _description = "Follow-up Report"

    def _get_followup_report_columns_name(self):
        """
        Return the name of the columns of the follow-ups report
        """
        return [
            {},
            {'name': ('Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': ('Due Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': ('Origin'), 'style': 'text-align:center; white-space:nowrap;'},
            {'name': ('Customer Po No'), 'style': 'text-align:right; white-space:nowrap;'},
            {'name': ('Total Due'), 'class': 'number o_price_total', 'style': 'text-align:right; white-space:nowrap;'},
        ]

    def _get_followup_report_lines(self, options):
        """
        Compute and return the lines of the columns of the follow-ups report.
        """
        # Get date format for the lang
        partner = options.get('partner_id') and self.env['res.partner'].browse(options['partner_id']) or False
        if not partner:
            return []

        lang_code = partner.lang
        lines = []
        res = {}
        today = fields.Date.today()
        line_num = 0
        for l in partner.unreconciled_aml_ids.sorted().filtered(
                lambda aml: not aml.currency_id.is_zero(aml.amount_residual_currency)):
            if l.company_id == self.env.company and not l.blocked:
                currency = l.currency_id or l.company_id.currency_id
                if currency not in res:
                    res[currency] = []
                res[currency].append(l)
        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            for aml in aml_recs:
                # print(aml,'77777777777777777777777777777777777777777777777')
                amount = aml.amount_residual_currency if aml.currency_id else aml.amount_residual
                invoice_date = {
                    'name': format_date(self.env, aml.move_id.invoice_date or aml.date, lang_code=lang_code),
                    'class': 'date',
                    'style': 'white-space:nowrap;text-align:center;'
                }
                print(aml.customer_po_no, 'vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv')
                custmer_po = {
                    'name': aml.customer_po_no,
                    'style': 'text-align:right; white-space:normal;'
                }

                # print(invoice_date,'000000000000000000000000000000000000000000000000000000')
                date_due = format_date(self.env, aml.date_maturity or aml.move_id.invoice_date or aml.date,
                                       lang_code=lang_code)
                total += not aml.blocked and amount or 0
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                is_payment = aml.payment_id
                if is_overdue or is_payment:
                    total_issued += not aml.blocked and amount or 0
                date_due = {'name': date_due, 'class': 'date', 'style': 'white-space:nowrap;text-align:center;'}
                print(date_due, '9999999999999999999999999999999999999999999999999999999999999999999')
                if is_overdue:
                    date_due['style'] += 'color: red;'
                if is_payment:
                    date_due = ''
                move_line_name = {
                    'name': self._followup_report_format_aml_name(aml.name, aml.move_id.ref),
                    'style': 'text-align:right; white-space:normal;'
                }
                print(move_line_name, "=============================================================")
                amount = formatLang(self.env, amount, currency_obj=currency)
                line_num += 1
                invoice_origin = aml.move_id.invoice_origin or ''
                if len(invoice_origin) > 43:
                    invoice_origin = invoice_origin[:40] + '...'
                invoice_origin = {
                    'name': invoice_origin,
                    'style': 'text-align:center; white-space:normal;',
                }
                columns = [
                    invoice_date,
                    date_due,
                    invoice_origin,
                    custmer_po,
                    # move_line_name,
                    amount,

                ]
                lines.append({
                    'id': aml.id,
                    'account_move': aml.move_id,
                    'name': aml.move_id.name,
                    'move_id': aml.move_id.id,
                    'type': is_payment and 'payment' or 'unreconciled_aml',
                    'unfoldable': False,
                    'columns': [isinstance(v, dict) and v or {'name': v} for v in columns],
                    'template': 'account_followup.cell_template_followup_report',
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
                'columns': [{'name': v} for v in [''] * 3 + [total >= 0 and _('Total Due') or '', total_due]],
                'template': 'account_followup.cell_template_followup_report',
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
                    'columns': [{'name': v} for v in [''] * 3 + [_('Total Overdue'), total_issued]],
                    'template': 'account_followup.cell_template_followup_report',
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
                'template': 'account_followup.cell_template_followup_report',
            })

        # Remove the last empty line
        if lines:
            lines.pop()
        print("++++++++++++++++++++++++++", lines)
        return lines