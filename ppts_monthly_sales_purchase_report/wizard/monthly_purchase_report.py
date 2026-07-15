from odoo import models, fields, api, _
import base64
from io import BytesIO
import xlsxwriter
import calendar
from datetime import date
from calendar import monthrange
from odoo.exceptions import ValidationError


class MonthlyPurchaseReport(models.TransientModel):
    _name = "monthly.purchase.report"
    _description = "Monthly Purchase Report"

    form_month = fields.Selection(
        [('jan', 'January'), ('feb', 'February'), ('mar', 'March'), ('apr', 'April'), ('may', 'May'), ('june', 'June'),
         ('july', 'July'), ('aug', 'August'), ('sep', 'September'), ('oct', 'October'), ('nov', 'November'),
         ('dec', 'December')], string="From Month")
    to_month = fields.Selection(
        [('jan', 'January'), ('feb', 'February'), ('mar', 'March'), ('apr', 'April'), ('may', 'May'), ('june', 'June'),
         ('july', 'July'), ('aug', 'August'), ('sep', 'September'), ('oct', 'October'), ('nov', 'November'),
         ('dec', 'December')], string="To Month")
    year_id = fields.Many2one('financial.year', string="Year")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)

    # show the monthly purchase invoice report
    def download_report(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Monthly Purchase Report')
        prod_title = workbook.add_format({
            'bold': True,
            'valign': 'vcenter',
            'font_size': 14,
            'align': 'center',
            'text_wrap': True,
            'bg_color': '#95B9C7',
        })
        prod_head = workbook.add_format({
            'bold': True,
            'valign': 'vcenter',
            'font_size': 12,
            'align': 'center',
            'bg_color': '#4F81BD',
            'font_color': '#FFFFFF',
            'text_wrap': True,
        })
        total_style = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'right',
            'bg_color': '#FFF2CC',
            'text_wrap': True,
        })
        total_amount_style = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'right',
            'bg_color': '#FFF2CC',
            'text_wrap': True,
            'num_format': '#,##0.00'
        })
        total_column = workbook.add_format({
            'align': 'right',
            'bg_color': '#FFF2CC',
            'text_wrap': True,
            'num_format': '#,##0.00',
            'text_wrap': True,
        })
        amount_format = workbook.add_format({
            'num_format': '#,##0.00',
            'text_wrap': True,
        })
        right_style = workbook.add_format({
            'align': 'right',
        })
        sheet.set_column(0, 0, 10)
        sheet.set_column(1, 1, 25)
        sheet.set_column(2, 2, 17)
        sheet.set_column(3, 3, 17)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 10)
        sheet.set_column(11, 11, 12)
        sheet.set_column(12, 12, 10)
        sheet.set_column(13, 13, 25)
        sheet.set_column(14, 14, 20)
        sheet.set_column(15, 15, 20)
        sheet.merge_range(0, 0, 0, 12, 'Monthly Purchase Report', prod_title)
        sheet.write(2, 0, 'Number', prod_head)
        sheet.write(2, 1, 'Invoice Partner Display Name', prod_head)
        sheet.write(2, 2, 'Invoice/Bill Date', prod_head)
        sheet.write(2, 3, 'Reference', prod_head)
        sheet.write(2, 4, 'Currency', prod_head)
        sheet.write(2, 5, 'Untaxed Amount', prod_head)
        sheet.write(2, 6, 'Tax', prod_head)
        sheet.write(2, 7, 'Company Currency', prod_head)
        sheet.write(2, 8, 'Untaxed Amount Signed', prod_head)
        sheet.write(2, 9, 'Tax Signed', prod_head)
        sheet.write(2, 10, 'Status', prod_head)
        sheet.write(2, 11, 'Payment', prod_head)
        sheet.write(2, 12, 'Month', prod_head)
        month_map = {
            'jan': 1,
            'feb': 2,
            'mar': 3,
            'apr': 4,
            'may': 5,
            'june': 6,
            'july': 7,
            'aug': 8,
            'sep': 9,
            'oct': 10,
            'nov': 11,
            'dec': 12,
        }
        year = int(self.year_id.name)
        from_month = month_map[self.form_month]
        to_month = month_map[self.to_month]
        if to_month < from_month:
            raise ValidationError(
                _("Please select a valid month. The 'To Month' should be later than or equal to the 'From Month'.")
            )
        from_date = date(year, from_month, 1)
        last_day = monthrange(year, to_month)[1]
        to_date = date(year, to_month, last_day)
        from_date_str = from_date.strftime('%Y/%m/%d')
        to_date_str = to_date.strftime('%Y/%m/%d')
        other_company_partners = [company.partner_id.id for company in
                                  self.env['res.company'].sudo().search([('id', '!=', self.company_id.id)]) if
                                  company.partner_id]
        pecko_usd_partner = self.env['res.partner'].sudo().search(
            [('company_id', '=', self.company_id.id), ('is_pecko_usd', '=', True)]) or False
        if pecko_usd_partner:
            other_company_partners.append(pecko_usd_partner.id)
        tax_account_move = self.env['account.move'].sudo().search(
            [('partner_id', 'not in', other_company_partners), ('invoice_date', '>=', from_date_str),
             ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
             ('move_type', 'in', ['in_invoice', 'in_refund']), ('amount_tax_signed', '!=', 0),('partner_id.trading_type','=','traders')]) or []
        sheet.freeze_panes(3, 0)
        row = 3
        # debit_journal = self.env['account.journal'].sudo().search(
        #     [('is_debit_journal', '=', True), ('company_id', '=', self.company_id.id)]).ids or []
        for move in tax_account_move:
            sheet.write(row, 0, move.name)
            sheet.write(row, 1, move.partner_id.name)
            sheet.write(row, 2, move.invoice_date.strftime('%d/%m/%Y'))
            sheet.write(row, 3, move.ref)
            sheet.write(row, 4, move.currency_id.name)
            if move.move_type == 'in_refund':
                sheet.write(row, 5, -abs(move.amount_untaxed), amount_format)
                sheet.write(row, 6, -abs(move.amount_tax), amount_format)
                sheet.write(row, 8, -abs(move.amount_untaxed_signed), amount_format)
                sheet.write(row, 9, -abs(move.amount_tax_signed), amount_format)
            else:
                sheet.write(row, 5, abs(move.amount_untaxed), amount_format)
                sheet.write(row, 6, move.amount_tax, amount_format)
                sheet.write(row, 8, abs(move.amount_untaxed_signed), amount_format)
                sheet.write(row, 9, move.amount_tax_signed, amount_format)
            sheet.write(row, 7, move.company_id.currency_id.name)
            sheet.write(row, 10, 'Posted')
            # sheet.write(row, 11, move.status_in_payment)
            status_label = dict(
                move._fields['status_in_payment'].selection
            ).get(move.status_in_payment)
            sheet.write(row, 11, status_label)
            sheet.write(row, 12, move.invoice_date.month if move.invoice_date else '')
            if abs(move.amount_tax_signed) > 0 and abs(move.amount_untaxed_signed) > 0:
                sheet.write(row, 13,str(round((abs(move.amount_tax_signed) / abs(move.amount_untaxed_signed)) * 100, 1)) + '%',right_style)
            row += 1
        if tax_account_move:
            sheet.merge_range(row + 1, 0, row + 1, 6, "Local", total_style)
            sheet.write(row + 1, 7, '', total_style)
            sheet.write(row + 1, 8,  round(sum(abs(move.amount_untaxed_signed) if move.move_type == 'in_invoice'
                else -abs(move.amount_untaxed_signed)
                for move in tax_account_move), 2), total_amount_style)
            sheet.write(row + 1, 9, round(sum(move.amount_tax_signed if move.move_type == 'in_invoice'
                else -abs(move.amount_tax_signed)
                for move in tax_account_move), 2), total_amount_style)
            sheet.write(row + 1, 10, '', total_style)
            sheet.write(row + 1, 11, '', total_style)
            sheet.write(row + 1, 12, '', total_style)
            row += 2
        nontax_account_move = self.env['account.move'].sudo().search(
            [('partner_id', 'not in', other_company_partners), ('invoice_date', '>=', from_date_str),
             ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
             ('move_type', 'in', ['in_invoice', 'in_refund']), ('amount_tax_signed', '=', 0),('partner_id.trading_type','=','traders')]) or []
        if nontax_account_move:
            sheet.merge_range(row + 1, 0, row + 1, 12, "Import", prod_head)
            row += 2
        for nontax_move in nontax_account_move:
            sheet.write(row, 0, nontax_move.name)
            sheet.write(row, 1, nontax_move.partner_id.name)
            sheet.write(row, 2, nontax_move.invoice_date.strftime('%d/%m/%Y'))
            sheet.write(row, 3, nontax_move.ref)
            sheet.write(row, 4, nontax_move.currency_id.name)
            if nontax_move.move_type == 'in_refund':
                sheet.write(row, 5, -abs(nontax_move.amount_untaxed), amount_format)
                sheet.write(row, 8, -abs(nontax_move.amount_untaxed_signed), amount_format)
                # sheet.write(row, 6, -move.amount_tax)
            else:
                sheet.write(row, 5, abs(nontax_move.amount_untaxed), amount_format)
                sheet.write(row, 8, abs(nontax_move.amount_untaxed_signed), amount_format)
                # sheet.write(row, 6, move.amount_tax)
            sheet.write(row, 7, nontax_move.company_id.currency_id.name)
            # sheet.write(row, 9, move.amount_tax_signed)
            sheet.write(row, 10, 'Posted')
            status_label = dict(
                nontax_move._fields['status_in_payment'].selection
            ).get(nontax_move.status_in_payment)
            sheet.write(row, 11, status_label)
            sheet.write(row, 12, nontax_move.invoice_date.month if nontax_move.invoice_date else '')
            row += 1
        if nontax_account_move:
            sheet.merge_range(row + 1, 0, row + 1, 7, "Import", total_style)
            sheet.write(row + 1, 8,  round(sum(abs(move.amount_untaxed_signed) if move.move_type == 'in_invoice'
                      else -abs(move.amount_untaxed_signed)
                      for move in nontax_account_move), 2),
                        total_amount_style)
            sheet.write(row + 1, 9, '', total_style)
            sheet.write(row + 1, 10, '', total_style)
            sheet.write(row + 1, 11, '', total_style)
            sheet.write(row + 1, 12, '', total_style)
            row += 3
        malaysia_company = self.env['res.company'].search([('partner_id.country_id.code', '=', 'MY')], limit=1)
        malaysia_records = []
        if malaysia_company and pecko_usd_partner:
            malaysia_records = self.env['account.move'].sudo().search(
                [('partner_id', '=', pecko_usd_partner.id), ('invoice_date', '>=', from_date_str),
                 ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                 ('move_type', 'in', ['in_invoice', 'in_refund']), ('amount_tax_signed', '=', 0)]) or []
            if malaysia_records != []:
                sheet.merge_range(row, 0, row, 12, "PM", prod_head)
                row += 1
            for malaysia_move in malaysia_records:
                sheet.write(row, 0, malaysia_move.name)
                sheet.write(row, 1, malaysia_move.partner_id.name)
                sheet.write(row, 2, malaysia_move.invoice_date.strftime('%d/%m/%Y'))
                sheet.write(row, 3, malaysia_move.ref)
                sheet.write(row, 4, malaysia_move.currency_id.name)
                if malaysia_move.move_type == 'in_refund':
                    sheet.write(row, 5, -abs(malaysia_move.amount_untaxed), amount_format)
                    sheet.write(row, 8, -abs(malaysia_move.amount_untaxed_signed), amount_format)
                else:
                    sheet.write(row, 5, abs(malaysia_move.amount_untaxed), amount_format)
                    sheet.write(row, 8, abs(malaysia_move.amount_untaxed_signed), amount_format)
                sheet.write(row, 7, malaysia_move.company_id.currency_id.name)
                # sheet.write(row, 9, malaysia_move.amount_tax_signed)
                sheet.write(row, 10, 'Posted')
                status_label = dict(
                    malaysia_move._fields['status_in_payment'].selection
                ).get(malaysia_move.status_in_payment)
                sheet.write(row, 11, status_label)
                sheet.write(row, 12, malaysia_move.invoice_date.month if malaysia_move.invoice_date else '')
                row += 1
        if malaysia_company and malaysia_records != []:
            sheet.merge_range(row, 0, row, 4, "PM", total_style)
            sheet.write(row, 5, round(sum(abs(move.amount_untaxed) if move.move_type == 'in_invoice'
                else -abs(move.amount_untaxed)
                for move in malaysia_records), 2), total_amount_style)
            sheet.write(row, 8, round(sum(abs(mal_move.amount_untaxed_signed) if mal_move.move_type == 'in_invoice'
                else -abs(mal_move.amount_untaxed_signed)
                for mal_move in malaysia_records), 2), total_amount_style)
            sheet.write(row, 6, '', total_style)
            sheet.write(row, 7, '', total_style)
            sheet.write(row, 9, '', total_style)
            sheet.write(row, 10, '', total_style)
            sheet.write(row, 11, '', total_style)
            sheet.write(row, 12, '', total_style)
            row += 3
        singapore_company = self.env['res.company'].search(
            [('partner_id.country_id.code', '=', 'SG'), ('id', '!=', self.company_id.id)], limit=1)
        singapore_records = []
        if singapore_company:
            singapore_records = self.env['account.move'].sudo().search(
                [('partner_id', '=', singapore_company.partner_id.id), ('invoice_date', '>=', from_date_str),
                 ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                 ('move_type', 'in', ['in_invoice', 'in_refund']), ('amount_tax_signed', '!=', 0)]) or []
            if singapore_records != []:
                sheet.merge_range(row, 0, row, 12, "AWS/PH", prod_head)
                row += 1
            for singapore_move in singapore_records:
                sheet.write(row, 0, singapore_move.name)
                sheet.write(row, 1, singapore_move.partner_id.name)
                sheet.write(row, 2, singapore_move.invoice_date.strftime('%d/%m/%Y'))
                sheet.write(row, 3, singapore_move.ref)
                sheet.write(row, 4, singapore_move.currency_id.name)
                if singapore_move.move_type == 'in_refund':
                    sheet.write(row, 5, -abs(singapore_move.amount_untaxed), amount_format)
                    sheet.write(row, 6, -abs(singapore_move.amount_tax), amount_format)
                    sheet.write(row, 8, -abs(singapore_move.amount_untaxed_signed), amount_format)
                    sheet.write(row, 9, -abs(singapore_move.amount_tax_signed), amount_format)
                else:
                    sheet.write(row, 5, abs(singapore_move.amount_untaxed), amount_format)
                    sheet.write(row, 6, singapore_move.amount_tax, amount_format)
                    sheet.write(row, 8, abs(singapore_move.amount_untaxed_signed), amount_format)
                    sheet.write(row, 9, singapore_move.amount_tax_signed, amount_format)
                sheet.write(row, 7, singapore_move.company_id.currency_id.name)
                sheet.write(row, 10, 'Posted')
                status_label = dict(
                    singapore_move._fields['status_in_payment'].selection
                ).get(singapore_move.status_in_payment)
                sheet.write(row, 11, status_label)
                sheet.write(row, 12, singapore_move.invoice_date.month if singapore_move.invoice_date else '')
                if abs(move.amount_tax_signed) > 0 and abs(move.amount_untaxed_signed) > 0:
                    sheet.write(row, 13,
                                str(round((abs(move.amount_tax_signed) / abs(move.amount_untaxed_signed)) * 100,
                                          1)) + '%', right_style)
                row += 1
        if singapore_company and singapore_records != []:
            sheet.merge_range(row, 0, row, 4, "AWS Total", total_style)
            sheet.write(row, 5, round(sum(abs(move.amount_untaxed) if move.move_type == 'in_invoice'
                      else --abs(move.amount_untaxed)
                      for move in singapore_records), 2), total_amount_style)
            sheet.write(row, 6, round(sum(move.amount_tax if move.move_type == 'in_invoice'
                      else -abs(move.amount_tax)
                      for move in singapore_records), 2), total_amount_style)
            sheet.write(row, 7, '', total_style)
            sheet.write(row, 8,round(sum(abs(move.amount_untaxed_signed) if move.move_type == 'in_invoice'
                      else -abs(move.amount_untaxed_signed)
                      for move in singapore_records), 2), total_amount_style)
            sheet.write(row, 9, round(sum(move.amount_tax_signed if move.move_type == 'in_invoice'
                      else -abs(move.amount_tax_signed)
                      for move in singapore_records), 2), total_amount_style)
            sheet.write(row, 10, '', total_style)
            sheet.write(row, 11, '', total_style)
            sheet.write(row, 12, '', total_style)
            row += 2
        taxable_expense_records = self.env['account.move'].sudo().search(
            [('partner_id.trading_type','=','non_traders'), ('invoice_date', '>=', from_date_str),
             ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
             ('move_type', 'in', ['in_invoice', 'in_refund']), ('amount_tax_signed', '=', 0)]) or []
        if taxable_expense_records != []:
            sheet.merge_range(row, 0, row, 12, "Taxable Expenses", prod_head)
            row += 1
        for taxable_expense_move in taxable_expense_records:
            sheet.write(row, 0, taxable_expense_move.name)
            sheet.write(row, 1, taxable_expense_move.partner_id.name)
            sheet.write(row, 2, taxable_expense_move.invoice_date.strftime('%d/%m/%Y'))
            sheet.write(row, 3, taxable_expense_move.ref)
            sheet.write(row, 4, taxable_expense_move.currency_id.name)
            if taxable_expense_move.move_type == 'in_refund':
                sheet.write(row, 5, -abs(taxable_expense_move.amount_untaxed), amount_format)
                sheet.write(row, 8, -abs(taxable_expense_move.amount_untaxed_signed), amount_format)
                # sheet.write(row, 6, -taxable_expense_move.amount_tax)
            else:
                sheet.write(row, 5, abs(taxable_expense_move.amount_untaxed), amount_format)
                sheet.write(row, 8, abs(taxable_expense_move.amount_untaxed_signed), amount_format)
                # sheet.write(row, 6, taxable_expense_move.amount_tax)
            sheet.write(row, 7, taxable_expense_move.company_id.currency_id.name)
            # sheet.write(row, 9, taxable_expense_move.amount_tax_signed)
            sheet.write(row, 10, 'Posted')
            status_label = dict(
                taxable_expense_move._fields['status_in_payment'].selection
            ).get(taxable_expense_move.status_in_payment)
            sheet.write(row, 11, status_label)
            sheet.write(row, 12, taxable_expense_move.invoice_date.month if taxable_expense_move.invoice_date else '')
            row += 1
        if taxable_expense_records != []:
            sheet.merge_range(row, 0, row, 4, "Total", total_style)
            sheet.write(row, 5, round(sum(abs(move.amount_untaxed) if move.move_type == 'in_invoice'
                      else -abs(move.amount_untaxed)
                      for move in taxable_expense_records), 2), total_amount_style)
            sheet.write(row, 6, '', total_style)
            sheet.write(row, 7, '', total_style)
            sheet.write(row, 8, round(sum(abs(move.amount_untaxed_signed) if move.move_type == 'in_invoice'
                      else -abs(move.amount_untaxed_signed)
                      for move in taxable_expense_records), 2),
                        total_amount_style)
            sheet.write(row, 9, '', total_style)
            sheet.write(row, 10, '', total_style)
            sheet.write(row, 11, '', total_style)
            sheet.write(row, 12, '', total_style)
            row += 1
        row += 2
        freighters_records = self.env['account.move'].sudo().search(
            [('partner_id.trading_type', '=', 'transport'), ('invoice_date', '>=', from_date_str),
             ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
             ('move_type', 'in', ['in_invoice', 'in_refund']), ('amount_tax_signed', '=', 0)]) or []
        if freighters_records != []:
            sheet.merge_range(row, 0, row, 12, "Freighters", prod_head)
            row += 1
        for freighter_move in freighters_records:
            sheet.write(row, 0, freighter_move.name)
            sheet.write(row, 1, freighter_move.partner_id.name)
            sheet.write(row, 2, freighter_move.invoice_date.strftime('%d/%m/%Y'))
            sheet.write(row, 3, freighter_move.ref)
            sheet.write(row, 4, freighter_move.currency_id.name)
            if freighter_move.move_type == 'in_refund':
                sheet.write(row, 5, -abs(freighter_move.amount_untaxed), amount_format)
                sheet.write(row, 8, -abs(freighter_move.amount_untaxed_signed), amount_format)
                # sheet.write(row, 6, -freighter_move.amount_tax)
            else:
                sheet.write(row, 5, abs(freighter_move.amount_untaxed), amount_format)
                sheet.write(row, 8, abs(freighter_move.amount_untaxed_signed), amount_format)
                # sheet.write(row, 6, freighter_move.amount_tax)
            sheet.write(row, 7, freighter_move.company_id.currency_id.name)
            # sheet.write(row, 9, freighter_move.amount_tax_signed)
            sheet.write(row, 10, 'Posted')
            status_label = dict(
                freighter_move._fields['status_in_payment'].selection
            ).get(freighter_move.status_in_payment)
            sheet.write(row, 11, status_label)
            sheet.write(row, 12, freighter_move.invoice_date.month if freighter_move.invoice_date else '')
            row += 1
        if freighters_records != []:
            sheet.merge_range(row, 0, row, 4, "Total", total_style)
            sheet.write(row, 5, round(sum(abs(move.amount_untaxed) if move.move_type == 'in_invoice'
                                          else -abs(move.amount_untaxed)
                                          for move in freighters_records), 2), total_amount_style)
            sheet.write(row, 6, '', total_style)
            sheet.write(row, 7, '', total_style)
            sheet.write(row, 8, round(sum(abs(move.amount_untaxed_signed) if move.move_type == 'in_invoice'
                                          else -abs(move.amount_untaxed_signed)
                                          for move in freighters_records), 2),
                        total_amount_style)
            sheet.write(row, 9, '', total_style)
            sheet.write(row, 10, '', total_style)
            sheet.write(row, 11, '', total_style)
            sheet.write(row, 12, '', total_style)
            row += 1
        row += 2
        sheet.write(row, 1, 'Purchase' + '  ' + self.year_id.name, prod_title)
        # sheet.write(row, 13, "US DOLLAR", prod_title)
        sheet.write(row + 1, 2, 'Local ' + str(self.company_id.currency_id.symbol), prod_head)
        sheet.write(row + 1, 3, 'Export ' + str(self.company_id.currency_id.symbol), prod_head)
        sheet.write(row + 1, 4, '3rd party Purchases ' + str(self.company_id.currency_id.symbol), prod_head)
        sheet.write(row + 1, 5, 'PM ' + str(self.company_id.currency_id.symbol), prod_head)
        sheet.write(row + 1, 6, 'AWS ' + str(self.company_id.currency_id.symbol), prod_head)
        sheet.write(row + 1, 7, 'Total Purchases ' + str(self.company_id.currency_id.symbol), prod_head)
        sheet.write(row + 1, 8,
                    'Taxable Expenses',
                    prod_head)
        sheet.write(row + 1, 9, '3rd party GST ' + str(self.company_id.currency_id.symbol), prod_head)
        sheet.write(row + 1, 10, 'AWS GST ' + str(self.company_id.currency_id.symbol), prod_head)
        sheet.write(row + 1, 11, 'Taxable Exp ' + str(self.company_id.currency_id.symbol), prod_head)
        sheet.write(row + 1, 12, 'Bank Paid & Giro GST $',prod_head)
        sheet.write(row + 1, 13, 'Total GST',prod_head)
        row += 2
        total_local_sales = total_export_sales = total_third_purchase = total_pm_sales = total_aws_sales = total_purchases = total_expenses = total_3rdparty_expense = tot_singapore_gst_sales_amount = total_taxable_expense = total_bank_paid = total_gst_purchase = 0
        for i in range(from_month-1, to_month):
            moth_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            month = moth_list[i]
            sheet.write(row, 1, month)
            year = int(self.year_id.name)
            from_date = date(year, i + 1, 1)
            last_day = monthrange(year, i + 1)[1]
            to_date = date(year, i + 1, last_day)
            from_date_str = from_date.strftime('%Y/%m/%d')
            to_date_str = to_date.strftime('%Y/%m/%d')
            local_sales_amount = export_sales_amount = malaysia_sales_amount = singapore_sales_amount = local_sales_gst_amount = singapore_gst_sales_amount = 0
            local_mothwise_moves = self.env['account.move'].sudo().search(
                [('partner_id', 'not in', other_company_partners), ('invoice_date', '>=', from_date_str),
                 ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                 ('move_type', 'in', ['in_invoice', 'in_refund']), ('amount_tax_signed', '!=', 0),('partner_id.trading_type','=','traders')]) or []
            if local_mothwise_moves != []:
                local_sales_amount =  round(sum(abs(move.amount_untaxed_signed) if move.move_type == 'in_invoice'
                          else -abs(move.amount_untaxed_signed)
                          for move in local_mothwise_moves), 2)
                local_sales_gst_amount = round(sum(move.amount_tax_signed if move.move_type == 'in_invoice'
                          else -abs(move.amount_tax_signed)
                          for move in local_mothwise_moves), 2)
                total_local_sales += local_sales_amount
                total_3rdparty_expense += local_sales_gst_amount
                sheet.write(row, 2, local_sales_amount, amount_format)
                sheet.write(row, 9, local_sales_gst_amount, amount_format)
            export_account_move = self.env['account.move'].sudo().search(
                [('partner_id', 'not in', other_company_partners), ('invoice_date', '>=', from_date_str),
                 ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                 ('move_type', 'in', ['in_invoice', 'in_refund']), ('amount_tax_signed', '=', 0),('partner_id.trading_type','=','traders')]) or []
            if export_account_move != []:
                export_sales_amount =  round(sum(abs(move.amount_untaxed_signed) if move.move_type == 'in_invoice'
                          else -abs(move.amount_untaxed_signed)
                          for move in export_account_move), 2)
                total_export_sales += export_sales_amount
                sheet.write(row, 3, export_sales_amount,  amount_format)
            third_party = local_sales_amount + export_sales_amount
            total_third_purchase += third_party
            sheet.write(row, 4, third_party, total_column)
            malaysia_sales = self.env['account.move'].sudo().search(
                [('partner_id', '=', pecko_usd_partner.id), ('invoice_date', '>=', from_date_str),
                 ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                 ('move_type', 'in', ['in_invoice', 'in_refund']), ('amount_tax_signed', '=', 0)]) or []
            if malaysia_sales != []:
                # malaysia_sales_amount = round(sum(malaysia_sales.mapped('amount_untaxed_signed')), 2)
                malaysia_sales_amount = round(sum(
                    abs(move.amount_untaxed_signed) if move.move_type == 'in_invoice'
                    else -abs(move.amount_untaxed_signed)
                    for move in malaysia_sales
                ), 2)
                total_pm_sales += malaysia_sales_amount
                sheet.write(row, 5, malaysia_sales_amount, amount_format)
            if singapore_company:
                singapo_records = self.env['account.move'].sudo().search(
                [('partner_id', '=', singapore_company.partner_id.id), ('invoice_date', '>=', from_date_str),
                 ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                 ('move_type', 'in', ['in_invoice', 'in_refund']), ('amount_tax_signed', '!=', 0)]) or []
                singapore_amount = round(sum(abs(move.amount_untaxed_signed) if move.move_type == 'in_invoice'
                      else -abs(move.amount_untaxed_signed)
                      for move in singapo_records), 2)
                singapore_gst_amount = round(sum(move.amount_tax_signed if move.move_type == 'in_invoice'
                                                       else -abs(move.amount_tax_signed)
                                                       for move in singapo_records), 2)
                total_aws_sales += singapore_amount
                sheet.write(row, 6, singapore_amount, amount_format)
                tot_singapore_gst_sales_amount += singapore_gst_amount
                sheet.write(row, 10, singapore_gst_amount, amount_format)
            tot_purchase = third_party + singapore_amount
            sheet.write(row, 7, singapore_amount, amount_format)
            total_purchases += tot_purchase
            tax_expense_records = self.env['account.move'].sudo().search(
                [('partner_id.trading_type', '=', 'non_traders'), ('invoice_date', '>=', from_date_str),
                 ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                 ('move_type', 'in', ['in_invoice', 'in_refund']), ('amount_tax_signed', '=', 0)]) or []
            tax_exp_amount = round(sum(abs(move.amount_untaxed_signed) if move.move_type == 'in_invoice'
                      else -abs(move.amount_untaxed_signed)
                      for move in tax_expense_records), 2)
            tax_exp_gst_amount = round(sum(move.amount_tax_signed if move.move_type == 'in_invoice'
                      else -abs(move.amount_tax_signed)
                      for move in tax_expense_records), 2)
            sheet.write(row, 8, tax_exp_amount, amount_format)
            sheet.write(row, 11, tax_exp_gst_amount, amount_format)
            total_expenses += tax_exp_amount
            total_taxable_expense += tax_exp_gst_amount
            total_gst = third_party
            gst_purchase  = local_sales_gst_amount
            total_gst_purchase += gst_purchase
            sheet.write(row, 13, gst_purchase, amount_format)
            row += 1
        sheet.write(row, 1, "Total", total_style)
        sheet.write(row, 2, total_local_sales, total_amount_style)
        sheet.write(row, 3, total_export_sales, total_amount_style)
        sheet.write(row, 4, total_third_purchase, total_amount_style)
        sheet.write(row, 5, total_pm_sales, total_amount_style)
        sheet.write(row, 6, total_aws_sales, total_amount_style)
        sheet.write(row, 7, total_purchases, total_amount_style)
        sheet.write(row, 8, total_expenses, total_amount_style)
        sheet.write(row, 9, total_3rdparty_expense, total_amount_style)
        sheet.write(row, 10, tot_singapore_gst_sales_amount, total_amount_style)
        sheet.write(row, 11, total_taxable_expense, total_amount_style)
        sheet.write(row, 12, total_bank_paid, total_amount_style)
        sheet.write(row, 13, total_gst_purchase, total_amount_style)
        workbook.close()
        output.seek(0)
        file_data = output.getvalue()
        output.close()
        report_name = 'Monthly Purchase Report.xlsx'
        attach_id = self.env['ir.attachment'].sudo().create({
            'name': report_name,
            'type': 'binary',
            'public': True,
            'datas': base64.b64encode(file_data),
        })
        url = f"/web/content/?model=ir.attachment&id={attach_id.id}&filename_field=name&field=datas&download=true&"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
