from odoo import models, fields, api, _
import base64
from io import BytesIO
import xlsxwriter
import calendar
from datetime import date
from calendar import monthrange
from odoo.exceptions import ValidationError


class MonthlySalesReport(models.TransientModel):
    _name = "monthly.sales.report"
    _description = "Monthly Sales Report"

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

    # show the monthly sales invoice report
    def download_report(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        if self.company_id.is_aws_company:
            sheet = workbook.add_worksheet('AWS Sales Report')
        else:
            sheet = workbook.add_worksheet('Monthly Sales Report')
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
        if self.company_id.is_aws_company:
            sheet.merge_range(0, 0, 0, 12, 'AWS Sales Report', prod_title)
        else:
            sheet.merge_range(0, 0, 0, 12, 'Monthly Sales Report', prod_title)
        sheet.write(2, 0, 'Number', prod_head)
        sheet.write(2, 1, 'Invoice Partner Display Name', prod_head)
        sheet.write(2, 2, 'Invoice/Bill Date', prod_head)
        sheet.write(2, 3, 'Reference', prod_head)
        sheet.write(2, 4, 'Currency', prod_head)
        sheet.write(2, 5, 'Untaxed Amount', prod_head)
        sheet.write(2, 6, 'Tax', prod_head)
        sheet.write(2, 7, 'LOC Currency', prod_head)
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
        if self.company_id.is_aws_company:
            tax_account_move = self.env['account.move'].sudo().search(
                [('invoice_date', '>=', from_date_str),
                 ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                 ('move_type', 'in', ['out_invoice', 'out_refund'])]) or []
            pei_partners = tax_account_move.mapped('partner_id').filtered(lambda l:l.country_id.code == 'SG') or False
            pks_partners = tax_account_move.mapped('partner_id').filtered(lambda l:l.country_id.code != 'SG') or False
            pei_records =  self.env['account.move'].sudo().search([('partner_id','in',pei_partners.ids),('invoice_date', '>=', from_date_str),
                 ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                 ('move_type', 'in', ['out_invoice', 'out_refund'])]) or []
            row = 3
            for move in pei_records:
                sheet.write(row, 0, move.name)
                sheet.write(row, 1, move.partner_id.name)
                sheet.write(row, 2, move.invoice_date.strftime('%d/%m/%Y'))
                sheet.write(row, 3,  move.ref if move.ref else '')
                sheet.write(row, 4, move.currency_id.name)
                if move.move_type == 'out_refund':
                    sheet.write(row, 5, -abs(move.amount_untaxed), amount_format)
                    sheet.write(row, 6, -abs(move.amount_tax), amount_format)
                    sheet.write(row, 8, -abs(move.amount_untaxed_signed), amount_format)
                    sheet.write(row, 9, -abs(move.amount_tax_signed), amount_format)
                else:
                    sheet.write(row, 5, move.amount_untaxed, amount_format)
                    sheet.write(row, 6, move.amount_tax, amount_format)
                    sheet.write(row, 8, move.amount_untaxed_signed, amount_format)
                    sheet.write(row, 9, move.amount_tax_signed, amount_format)
                sheet.write(row, 7, move.company_id.currency_id.name)
                sheet.write(row, 10, 'Posted')
                # sheet.write(row, 11, move.status_in_payment)
                status_label = dict(
                    move._fields['status_in_payment'].selection
                ).get(move.status_in_payment)
                sheet.write(row, 11, status_label)
                sheet.write(row, 12, move.invoice_date.month if move.invoice_date else '')
                row += 1
            if pei_records != []:
                sheet.merge_range(row + 1, 0, row + 1, 6, "PEI", total_style)
                sheet.write(row + 1, 7, '', total_style)
                sheet.write(row + 1, 8, round(sum(move.amount_untaxed_signed if move.move_type == 'out_invoice'
                                                  else -abs(move.amount_untaxed_signed)
                                                  for move in pei_records), 2), total_amount_style)
                sheet.write(row + 1, 9, round(sum(move.amount_tax_signed if move.move_type == 'out_invoice'
                                                  else -abs(move.amount_tax_signed)
                                                  for move in pei_records), 2), total_amount_style)
                sheet.write(row + 1, 10, '', total_style)
                sheet.write(row + 1, 11, '', total_style)
                sheet.write(row + 1, 12, '', total_style)
                row += 4
            pks_records = self.env['account.move'].sudo().search([('partner_id','in',pks_partners.ids),('invoice_date', '>=', from_date_str),
                 ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                 ('move_type', 'in', ['out_invoice', 'out_refund'])]) or []
            if pks_records != []:
                sheet.merge_range(row, 0, row, 12, "PKS", prod_head)
                row += 1
            for move in pks_records:
                sheet.write(row, 0, move.name)
                sheet.write(row, 1, move.partner_id.name)
                sheet.write(row, 2, move.invoice_date.strftime('%d/%m/%Y'))
                sheet.write(row, 3, move.ref if move.ref else '')
                sheet.write(row, 4, move.currency_id.name)
                if move.move_type == 'out_refund':
                    sheet.write(row, 5, -abs(move.amount_untaxed), amount_format)
                    sheet.write(row, 8, -abs(move.amount_untaxed_signed), amount_format)
                else:
                    sheet.write(row, 5, move.amount_untaxed, amount_format)
                    sheet.write(row, 8, move.amount_untaxed_signed, amount_format)
                sheet.write(row, 7, move.company_id.currency_id.name)
                sheet.write(row, 10, 'Posted')
                status_label = dict(
                    move._fields['status_in_payment'].selection
                ).get(move.status_in_payment)
                sheet.write(row, 11, status_label)
                sheet.write(row, 12, move.invoice_date.month if move.invoice_date else '')
                row += 1
            if pks_records != []:
                sheet.merge_range(row + 1, 0, row + 1, 6, "PKS", total_style)
                sheet.write(row + 1, 7, '', total_style)
                sheet.write(row + 1, 8, round(sum(move.amount_untaxed_signed if move.move_type == 'out_invoice'
                                                  else -abs(move.amount_untaxed_signed)
                                                  for move in pks_records), 2), total_amount_style)
                row += 3
            sheet.write(row, 1, 'sales' + '  ' + self.year_id.name, prod_title)
            sheet.write(row + 1, 2, 'PEI S ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 3, 'PKS S ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 4, 'Sales S ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 5, 'Total Sales in S ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 6, 'GST S ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 7, 'Total GST S ' + str(self.company_id.currency_id.symbol), prod_head)
            total_pei_sales = total_pks_sales = total_sales = tot_sales = total_gst = tot_gst = 0
            row += 2
            for i in range(from_month - 1, to_month):
                moth_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                month = moth_list[i]
                sheet.write(row, 1, month)
                year = int(self.year_id.name)
                from_date = date(year, i + 1, 1)
                last_day = monthrange(year, i + 1)[1]
                to_date = date(year, i + 1, last_day)
                from_date_str = from_date.strftime('%Y/%m/%d')
                to_date_str = to_date.strftime('%Y/%m/%d')
                pei_rec = self.env['account.move'].sudo().search([('partner_id','in',pei_partners.ids),('invoice_date', '>=', from_date_str),
                 ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                 ('move_type', 'in', ['out_invoice', 'out_refund'])]) or []
                month_sale_total = 0
                if pei_rec != []:
                    pei_amount = round(sum(move.amount_untaxed_signed if move.move_type == 'out_invoice'
                              else -abs(move.amount_untaxed_signed)
                              for move in pei_rec), 2)
                    sheet.write(row, 2, pei_amount, amount_format)
                    total_pei_sales += pei_amount
                    month_sale_total += pei_amount
                    pei_gst_amount = round(sum(move.amount_tax_signed if move.move_type == 'out_invoice'
                                                 else -abs(move.amount_tax_signed)
                                                 for move in pei_rec), 2)
                    sheet.write(row, 6, pei_gst_amount, amount_format)
                    sheet.write(row, 7, pei_gst_amount, amount_format)
                    total_gst += pei_gst_amount
                pks_rec = self.env['account.move'].sudo().search(
                    [('partner_id', 'in', pks_partners.ids), ('invoice_date', '>=', from_date_str),
                     ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'),
                     ('company_id', '=', self.company_id.id),
                     ('move_type', 'in', ['out_invoice', 'out_refund'])]) or []
                if pks_rec != []:
                    pks_amount = round(sum(move.amount_untaxed_signed if move.move_type == 'out_invoice'
                                           else -abs(move.amount_untaxed_signed)
                                           for move in pks_rec), 2)
                    sheet.write(row, 3, pks_amount, amount_format)
                    total_pks_sales += pei_amount
                    month_sale_total += pei_amount
                sheet.write(row,4,month_sale_total)
                total_sales += month_sale_total
                sheet.write(row,5,month_sale_total)
                row += 1
            sheet.write(row, 2, total_pei_sales,total_amount_style)
            sheet.write(row, 3, total_pks_sales,total_amount_style)
            sheet.write(row, 4, total_sales,total_amount_style)
            sheet.write(row, 5, total_sales,total_amount_style)
            sheet.write(row, 6, total_gst,total_amount_style)
            sheet.write(row, 7, total_gst,total_amount_style)
        else:
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
                 ('move_type', 'in', ['out_invoice', 'out_refund']), ('amount_tax_signed', '!=', 0)]) or []
            sheet.freeze_panes(3, 0)
            row = 3
            credit_journal = self.env['account.journal'].sudo().search(
                [('is_credit_journal', '=', True), ('company_id', '=', self.company_id.id)]).ids or []
            for move in tax_account_move:
                sheet.write(row, 0, move.name)
                sheet.write(row, 1, move.partner_id.name)
                sheet.write(row, 2, move.invoice_date.strftime('%d/%m/%Y'))
                sheet.write(row, 3,  move.ref if move.ref else '')
                sheet.write(row, 4, move.currency_id.name)
                if move.move_type == 'out_refund':
                    sheet.write(row, 5, -abs(move.amount_untaxed), amount_format)
                    sheet.write(row, 6, -abs(move.amount_tax), amount_format)
                    sheet.write(row, 8, -abs(move.amount_untaxed_signed), amount_format)
                    sheet.write(row, 9, -abs(move.amount_tax_signed), amount_format)
                else:
                    sheet.write(row, 5, move.amount_untaxed, amount_format)
                    sheet.write(row, 6, move.amount_tax, amount_format)
                    sheet.write(row, 8, move.amount_untaxed_signed, amount_format)
                    sheet.write(row, 9, move.amount_tax_signed, amount_format)
                sheet.write(row, 7, move.company_id.currency_id.name)
                sheet.write(row, 10, 'Posted')
                # sheet.write(row, 11, move.status_in_payment)
                status_label = dict(
                    move._fields['status_in_payment'].selection
                ).get(move.status_in_payment)
                sheet.write(row, 11, status_label)
                sheet.write(row, 12, move.invoice_date.month if move.invoice_date else '')
                row += 1
            if tax_account_move:
                sheet.merge_range(row + 1, 0, row + 1, 6, "Local", total_style)
                sheet.write(row + 1, 7, '', total_style)
                sheet.write(row + 1, 8,  round(sum(move.amount_untaxed_signed if move.move_type == 'out_invoice'
                    else -abs(move.amount_untaxed_signed)
                    for move in tax_account_move), 2), total_amount_style)
                sheet.write(row + 1, 9, round(sum(move.amount_tax_signed if move.move_type == 'out_invoice'
                    else -abs(move.amount_tax_signed)
                    for move in tax_account_move), 2), total_amount_style)
                sheet.write(row + 1, 10, '', total_style)
                sheet.write(row + 1, 11, '', total_style)
                sheet.write(row + 1, 12, '', total_style)
                row += 2
            nontax_account_move = self.env['account.move'].sudo().search(
                [('partner_id', 'not in', other_company_partners), ('invoice_date', '>=', from_date_str),
                 ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                 ('move_type', 'in', ['out_invoice', 'out_refund']), ('amount_tax_signed', '=', 0)]) or []
            if nontax_account_move:
                sheet.merge_range(row + 1, 0, row + 1, 12, "Export", prod_head)
                row += 2
            for nontax_move in nontax_account_move:
                sheet.write(row, 0, nontax_move.name)
                sheet.write(row, 1, nontax_move.partner_id.name)
                sheet.write(row, 2, nontax_move.invoice_date.strftime('%d/%m/%Y'))
                sheet.write(row, 3, nontax_move.ref if nontax_move.ref else '')
                sheet.write(row, 4, nontax_move.currency_id.name)
                if nontax_move.move_type == 'out_refund':
                    sheet.write(row, 5, -abs(nontax_move.amount_untaxed), amount_format)
                    sheet.write(row, 8, -abs(nontax_move.amount_untaxed_signed), amount_format)
                    # sheet.write(row, 6, -move.amount_tax)
                else:
                    sheet.write(row, 5, nontax_move.amount_untaxed, amount_format)
                    sheet.write(row, 8, nontax_move.amount_untaxed_signed, amount_format)
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
                sheet.merge_range(row + 1, 0, row + 1, 7, "Export", total_style)
                sheet.write(row + 1, 8,  round(sum(move.amount_untaxed_signed if move.move_type == 'out_invoice'
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
                     ('move_type', 'in', ['out_invoice', 'out_refund']), ('amount_tax_signed', '=', 0),
                     ('journal_id', 'not in', credit_journal)]) or []
                if malaysia_records != []:
                    sheet.merge_range(row, 0, row, 12, "PM", prod_head)
                    row += 1
                for malaysia_move in malaysia_records:
                    sheet.write(row, 0, malaysia_move.name)
                    sheet.write(row, 1, malaysia_move.partner_id.name)
                    sheet.write(row, 2, malaysia_move.invoice_date.strftime('%d/%m/%Y'))
                    sheet.write(row, 3, malaysia_move.ref if malaysia_move.ref else '')
                    sheet.write(row, 4, malaysia_move.currency_id.name)
                    if malaysia_move.move_type == 'out_refund':
                        sheet.write(row, 5, -abs(malaysia_move.amount_untaxed), amount_format)
                        sheet.write(row, 8, -abs(malaysia_move.amount_untaxed_signed), amount_format)
                    else:
                        sheet.write(row, 5, malaysia_move.amount_untaxed, amount_format)
                        sheet.write(row, 8, malaysia_move.amount_untaxed_signed, amount_format)
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
                sheet.write(row, 5, round(sum(move.amount_untaxed if move.move_type == 'out_invoice'
                    else -abs(move.amount_untaxed)
                    for move in malaysia_records), 2), total_amount_style)
                sheet.write(row, 8, round(sum(mal_move.amount_untaxed_signed if mal_move.move_type == 'out_invoice'
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
                     ('move_type', 'in', ['out_invoice', 'out_refund']), ('amount_tax_signed', '!=', 0),
                     ('journal_id', 'not in', credit_journal)]) or []
                if singapore_records != []:
                    sheet.merge_range(row, 0, row, 12, "AWS/PH", prod_head)
                    row += 1
                for singapore_move in singapore_records:
                    sheet.write(row, 0, singapore_move.name)
                    sheet.write(row, 1, singapore_move.partner_id.name)
                    sheet.write(row, 2, singapore_move.invoice_date.strftime('%d/%m/%Y'))
                    sheet.write(row, 3, singapore_move.ref if singapore_move.ref else '')
                    sheet.write(row, 4, singapore_move.currency_id.name)
                    if singapore_move.move_type == 'out_refund':
                        sheet.write(row, 5, -abs(singapore_move.amount_untaxed), amount_format)
                        sheet.write(row, 6, -abs(singapore_move.amount_tax), amount_format)
                        sheet.write(row, 8, -abs(singapore_move.amount_untaxed_signed), amount_format)
                        sheet.write(row, 9, -abs(singapore_move.amount_tax_signed), amount_format)
                    else:
                        sheet.write(row, 5, singapore_move.amount_untaxed, amount_format)
                        sheet.write(row, 6, singapore_move.amount_tax, amount_format)
                        sheet.write(row, 8, singapore_move.amount_untaxed_signed, amount_format)
                        sheet.write(row, 9, singapore_move.amount_tax_signed, amount_format)
                    sheet.write(row, 7, singapore_move.company_id.currency_id.name)
                    sheet.write(row, 10, 'Posted')
                    status_label = dict(
                        singapore_move._fields['status_in_payment'].selection
                    ).get(singapore_move.status_in_payment)
                    sheet.write(row, 11, status_label)
                    sheet.write(row, 12, singapore_move.invoice_date.month if singapore_move.invoice_date else '')
                    row += 1
            if singapore_company and singapore_records != []:
                sheet.merge_range(row, 0, row, 4, "AWS Total", total_style)
                sheet.write(row, 5, round(sum(move.amount_untaxed if move.move_type == 'out_invoice'
                          else --abs(move.amount_untaxed)
                          for move in singapore_records), 2), total_amount_style)
                sheet.write(row, 6, round(sum(move.amount_tax if move.move_type == 'out_invoice'
                          else -abs(move.amount_tax)
                          for move in singapore_records), 2), total_amount_style)
                sheet.write(row, 7, '', total_style)
                sheet.write(row, 8,round(sum(move.amount_untaxed_signed if move.move_type == 'out_invoice'
                          else -abs(move.amount_untaxed_signed)
                          for move in singapore_records), 2), total_amount_style)
                sheet.write(row, 9, round(sum(move.amount_tax_signed if move.move_type == 'out_invoice'
                          else -abs(move.amount_tax_signed)
                          for move in singapore_records), 2), total_amount_style)
                sheet.write(row, 10, '', total_style)
                sheet.write(row, 11, '', total_style)
                sheet.write(row, 12, '', total_style)
                row += 2
            if malaysia_company:
                malaysia_debit_records = self.env['account.move'].sudo().search(
                    [('partner_id', 'in', other_company_partners), ('invoice_date', '>=', from_date_str),
                     ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                     ('move_type', 'in', ['out_invoice', 'out_refund']), ('amount_tax_signed', '=', 0),
                     ('journal_id', 'in', credit_journal)]) or []
                if malaysia_debit_records != []:
                    sheet.merge_range(row, 0, row, 12, "Debit Note", prod_head)
                    row += 1
                for malaysia_move in malaysia_debit_records:
                    sheet.write(row, 0, malaysia_move.name)
                    sheet.write(row, 1, malaysia_move.partner_id.name)
                    sheet.write(row, 2, malaysia_move.invoice_date.strftime('%d/%m/%Y'))
                    sheet.write(row, 3, malaysia_move.ref if malaysia_move.ref else '')
                    sheet.write(row, 4, malaysia_move.currency_id.name)
                    if malaysia_move.move_type == 'out_refund':
                        sheet.write(row, 5, -abs(malaysia_move.amount_untaxed), amount_format)
                        sheet.write(row, 8, -abs(malaysia_move.amount_untaxed_signed), amount_format)
                        # sheet.write(row, 6, -malaysia_move.amount_tax)
                    else:
                        sheet.write(row, 5, malaysia_move.amount_untaxed, amount_format)
                        sheet.write(row, 8, malaysia_move.amount_untaxed_signed, amount_format)
                        # sheet.write(row, 6, malaysia_move.amount_tax)
                    sheet.write(row, 7, malaysia_move.company_id.currency_id.name)
                    # sheet.write(row, 9, malaysia_move.amount_tax_signed)
                    sheet.write(row, 10, 'Posted')
                    status_label = dict(
                        malaysia_move._fields['status_in_payment'].selection
                    ).get(malaysia_move.status_in_payment)
                    sheet.write(row, 11, status_label)
                    sheet.write(row, 12, malaysia_move.invoice_date.month if malaysia_move.invoice_date else '')
                    row += 1
            if malaysia_company and malaysia_debit_records != []:
                sheet.merge_range(row, 0, row, 4, "Total", total_style)
                sheet.write(row, 5, round(sum(move.amount_untaxed if move.move_type == 'out_invoice'
                          else -abs(move.amount_untaxed)
                          for move in malaysia_debit_records), 2), total_amount_style)
                sheet.write(row, 6, '', total_style)
                sheet.write(row, 7, '', total_style)
                sheet.write(row, 8, round(sum(move.amount_untaxed_signed if move.move_type == 'out_invoice'
                          else -abs(move.amount_untaxed_signed)
                          for move in malaysia_debit_records), 2),
                            total_amount_style)
                sheet.write(row, 9, '', total_style)
                sheet.write(row, 10, '', total_style)
                sheet.write(row, 11, '', total_style)
                sheet.write(row, 12, '', total_style)
                row += 1
            row += 2
            sheet.write(row, 1, 'sales' + '  ' + self.year_id.name, prod_title)
            sheet.write(row, 13, "US DOLLAR", prod_title)
            sheet.write(row + 1, 2, 'Local ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 3, 'Export ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 4, '3rd Party ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 5, 'PM ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 6, 'AWS ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 7, 'Interco ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 8,
                        'Total Sales ' + str(self.year_id.name) + ' in ' + str(self.company_id.currency_id.symbol),
                        prod_head)
            sheet.write(row + 1, 9, 'Local GST ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 10, 'AWS GST ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 11, 'Total GST ' + str(self.company_id.currency_id.symbol), prod_head)
            sheet.write(row + 1, 13, 'PM Sales US$',prod_head)
            sheet.write(row + 1, 14, 'AWS Sales US$',prod_head)
            sheet.write(row + 1, 15, 'AWS GST US$',prod_head)
            row += 2
            total_local_sales = total_export_sales = total_third_sales = total_pm_sales = total_us_dol_sales = total_aws_dol_sales = total_aws_sales = total_singapore_gst_amount = total_interco_sales = total_year_sales = total_local_gst = total_aws_gst_sales = total_gst_sales = 0
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
                     ('move_type', 'in', ['out_invoice', 'out_refund']), ('amount_tax_signed', '!=', 0)]) or []
                if local_mothwise_moves != []:
                    local_sales_amount =  round(sum(move.amount_untaxed_signed if move.move_type == 'out_invoice'
                              else -abs(move.amount_untaxed_signed)
                              for move in local_mothwise_moves), 2)
                    local_sales_gst_amount = round(sum(move.amount_tax_signed if move.move_type == 'out_invoice'
                              else -abs(move.amount_tax_signed)
                              for move in local_mothwise_moves), 2)
                    total_local_sales += local_sales_amount
                    total_local_gst += local_sales_gst_amount
                    sheet.write(row, 2, local_sales_amount, amount_format)
                    sheet.write(row, 9, local_sales_gst_amount, amount_format)
                export_account_move = self.env['account.move'].sudo().search(
                    [('partner_id', 'not in', other_company_partners), ('invoice_date', '>=', from_date_str),
                     ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                     ('move_type', 'in', ['out_invoice', 'out_refund']), ('amount_tax_signed', '=', 0)]) or []
                if export_account_move != []:
                    export_sales_amount =  round(sum(move.amount_untaxed_signed if move.move_type == 'out_invoice'
                              else -abs(move.amount_untaxed_signed)
                              for move in export_account_move), 2)
                    total_export_sales += export_sales_amount
                    sheet.write(row, 3, export_sales_amount,  amount_format)
                third_party = local_sales_amount + export_sales_amount
                total_third_sales += third_party
                sheet.write(row, 4, third_party, total_column)
                malaysia_sales = self.env['account.move'].sudo().search(
                    [('partner_id', '=', pecko_usd_partner.id), ('invoice_date', '>=', from_date_str),
                     ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                     ('move_type', 'in', ['out_invoice', 'out_refund']), ('amount_tax_signed', '=', 0),
                     ('journal_id', 'not in', credit_journal)]) or []
                if malaysia_sales != []:
                    # malaysia_sales_amount = round(sum(malaysia_sales.mapped('amount_untaxed_signed')), 2)
                    malaysia_sales_amount = round(sum(
                        move.amount_untaxed_signed if move.move_type == 'out_invoice'
                        else -abs(move.amount_untaxed_signed)
                        for move in malaysia_sales
                    ), 2)
                    total_pm_sales += malaysia_sales_amount
                    sheet.write(row, 5, malaysia_sales_amount, amount_format)
                    malaysia_us_dolar_amount = round(sum(
                        move.amount_untaxed if move.move_type == 'out_invoice'
                        else -abs(move.amount_untaxed)
                        for move in malaysia_sales
                    ), 2)
                    total_us_dol_sales += malaysia_us_dolar_amount
                    sheet.write(row, 13, malaysia_us_dolar_amount, amount_format)
                singapore_sales = self.env['account.move'].sudo().search(
                    [('partner_id', '=', singapore_company.partner_id.id), ('invoice_date', '>=', from_date_str),
                     ('invoice_date', '<=', to_date_str), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                     ('move_type', 'in', ['out_invoice', 'out_refund']), ('amount_tax_signed', '!=', 0),('journal_id', 'not in', credit_journal)]) or []
                if singapore_sales != []:
                    singapore_sales_amount =  round(sum(
                        move.amount_untaxed_signed if move.move_type == 'out_invoice'
                        else -abs(move.amount_untaxed_signed)
                        for move in singapore_sales
                    ), 2)
                    singapore_gst_sales_amount = round(sum(
                        move.amount_tax_signed if move.move_type == 'out_invoice'
                        else -abs(move.amount_tax_signed)
                        for move in singapore_sales
                    ), 2)
                    total_aws_sales += singapore_sales_amount
                    total_aws_gst_sales += singapore_gst_sales_amount
                    sheet.write(row, 6, singapore_sales_amount, amount_format)
                    sheet.write(row, 10, singapore_gst_sales_amount, amount_format)
                    singapore_us_dol_amount = round(sum(
                        move.amount_untaxed if move.move_type == 'out_invoice'
                        else -abs(move.amount_untaxed)
                        for move in singapore_sales
                    ), 2)
                    singapore_gst_amount = round(sum(
                        move.amount_tax if move.move_type == 'out_invoice'
                        else -abs(move.amount_tax)
                        for move in singapore_sales
                    ), 2)
                    total_aws_dol_sales += singapore_us_dol_amount
                    total_singapore_gst_amount += singapore_gst_amount
                    sheet.write(row, 14, singapore_us_dol_amount, amount_format)
                    sheet.write(row, 15, singapore_gst_amount, amount_format)
                sheet.write(row, 7, malaysia_sales_amount + singapore_sales_amount, total_column)
                interco = malaysia_sales_amount + singapore_sales_amount
                total_interco_sales += interco
                sheet.write(row, 8, third_party + interco, amount_format)
                total_year_sales += third_party + interco
                sheet.write(row, 11, local_sales_gst_amount + singapore_gst_sales_amount, total_column)
                total_gst_sales += local_sales_gst_amount + singapore_gst_sales_amount
                row += 1
            sheet.write(row, 1, "Total", total_style)
            sheet.write(row, 2, total_local_sales, total_amount_style)
            sheet.write(row, 3, total_export_sales, total_amount_style)
            sheet.write(row, 4, total_third_sales, total_amount_style)
            sheet.write(row, 5, total_pm_sales, total_amount_style)
            sheet.write(row, 6, total_aws_sales, total_amount_style)
            sheet.write(row, 7, total_interco_sales, total_amount_style)
            sheet.write(row, 8, total_year_sales, total_amount_style)
            sheet.write(row, 9, total_local_gst, total_amount_style)
            sheet.write(row, 10, total_aws_gst_sales, total_amount_style)
            sheet.write(row, 11, total_gst_sales, total_amount_style)
            sheet.write(row, 13, total_us_dol_sales, total_amount_style)
            sheet.write(row, 14, total_aws_dol_sales, total_amount_style)
            sheet.write(row, 15, total_singapore_gst_amount, total_amount_style)
        workbook.close()
        output.seek(0)
        file_data = output.getvalue()
        output.close()
        if self.company_id.is_aws_company:
            report_name = 'AWS Sales Report.xlsx'
        else:
            report_name = 'Monthly Sales Report.xlsx'
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
