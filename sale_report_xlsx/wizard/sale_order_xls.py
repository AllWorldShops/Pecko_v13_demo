# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from tracemalloc import stop
import xlwt
import base64
from io import StringIO
from odoo import api, fields, models, _
import platform
from datetime import datetime, date
from io import BytesIO
import calendar
from dateutil.relativedelta import relativedelta


class WizardWizards(models.TransientModel):
    _name = 'wizard.reports'
    _description = 'Sale Order wizard'
    
    name = fields.Char("Name")
    partner_ids = fields.Many2many("res.partner", string="Customers")
    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")
    move_data = fields.Char('Name', size=256)
    file_name = fields.Binary('Sales Order Excel Report', readonly=True)
    
    def _get_months(self, start_date, end_date):
        res = []
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        while start_date <= end_date:
            month_names = str(start_date.strftime('%m')) + '/' + str(start_date.strftime('%Y'))
            res.append({'month_name': month_names,
                        'months_details': str(start_date.strftime('%m')),
                        'year_name': str(start_date.strftime('%Y'))})
            start_date += relativedelta(months=+1)
        return res
    
    def _get_sale_analysis_summary(self, data, start_date, end_date, partnerid):
        res = []
        amount_sub_total = 0
        start_date = fields.Date.from_string(start_date)
        month_date = date(start_date.year, int(start_date.month), 1)
        end_date = fields.Date.from_string(end_date)
        diffrence = relativedelta(end_date,start_date).years * 12 + \
                    ((relativedelta(end_date,start_date).months) + 1) 
        for x in range(0, diffrence):
            res.append({'months_amount': 0.00,
                        'months_turnover': 0.00,
                        'months_name': int(month_date.strftime('%m')),
                        'year_name': int(month_date.strftime('%Y'))})
            month_date += relativedelta(months=+1)
        sale_order_ids = self.env['sale.order'].search([
            ('partner_id', '=', partnerid), 
            ('date_order', '<=', str(end_date)),
            ('date_order', '>=', str(start_date)),
            ('state', '!=', 'cancel')
        ])
        for order in sale_order_ids:
            date_from = fields.Datetime.from_string(order.date_order)
            date_from = fields.Datetime.context_timestamp(order, date_from).date()
            date_to = date_from + relativedelta(months=+1, day=1, days=-1)
            date_diffrence = relativedelta(date_to, date_from)
            sum_turnover = sum(line.qty_delivered * line.price_unit for line in order.order_line)
            for record in res:
                if int(date_from.strftime('%m')) == record.get('months_name') \
                and int(date_from.strftime('%Y')) == record.get('year_name'):
                    record['months_amount'] += order.amount_untaxed or 0.00
                    record['months_turnover'] += sum_turnover or 0.00
                    record['months_name'] = int(date_from.strftime('%m') or '')
        return res
    
    def _get_data_subtotal_amount(self, data):
        result = []
        partner_ids = self.env['res.partner'].browse(data['partner'])
        for partner in partner_ids:
            amount_totals = 0.0
            amount_turn_over = 0.0
            sale_analysis_summary_records = self._get_sale_analysis_summary(data, self.date_from, self.date_to, partner.id)
            for record in sale_analysis_summary_records:
                amount_totals += record['months_amount']
                amount_turn_over += record['months_turnover']
            result.append({'partner_id': partner.id, 'amount_totals': amount_totals,
                           'amount_turn_over': amount_turn_over})
        return result
    
    def get_data_from_report(self, data):
        res = []
        Partner = self.env['res.partner']
        if 'partner' in data:
            res.append({'data':[]})
            partner_ids = Partner.browse(data['partner'])
            for partner in partner_ids:
                res[0]['data'].append({
                    'partner_name': partner.name,
                    'partner_id': partner.id,
                    'display': self._get_sale_analysis_summary(data, self.date_from, self.date_to, partner.id),
                    'subtotal_datas': self._get_data_subtotal_amount(data),
                })
        return res
    

    # @api.multi
    def action_sale_report(self):
        self.ensure_one()
        [data] = self.read()
        file_name = 'Sale Order Report.xls'
        date_from = str(self.date_from) + ' 00:00:00'
        date_to = str(self.date_to) + ' 00:00:00'
        sale_ord_line = self.env['sale.order.line'].search([('order_id.date_order', '>=', date_from),('order_id.date_order', '<=', date_to)])
        partner = sale_ord_line.mapped('order_id.partner_id')
        workbook = xlwt.Workbook(encoding="UTF-8")
        style2 = xlwt.easyxf('font: name Times New Roman bold on;align: horiz center;', num_format_str='#,##0')
        style0 = xlwt.easyxf('font: name Times New Roman bold on;align: horiz right;', num_format_str='#,##0.00')
        style1 = xlwt.easyxf('font: name Times New Roman, bold on,height 250;', num_format_str='#,##0.00')
        format6 = xlwt.easyxf('font:bold True,name Calibri;align: horiz center')
        format4 = xlwt.easyxf('align: horiz right;font: name Calibri;')
        format1 = xlwt.easyxf('align: horiz center;font: name Calibri;')

        format2 = xlwt.easyxf('align: horiz left;font: name Calibri')
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy'
        sheet = workbook.add_sheet("Sale order", cell_overwrite_ok=True)
        start = self.date_from
        end = self.date_to

        for sale in sale_ord_line:
            date = sale.order_id.date_order.date()
            if start <= date <= end:
                sheet.write(0, 0, 'Customer Name', format6)
                sheet.write(0, 1, 'Turnover(T) or Intake(I)', format6)
                get_months_records = self._get_months(self.date_from, self.date_to)
                col = 2
                for g_months in get_months_records:
                    sheet.write(0, col, str(g_months['month_name']), format6)
                    sheet.write(0, col+1, "Turnover", format6)
                    sheet.write(0, col+2, "Intake", format6)
                    col += 1
                        
        i=2
        t=1
        k=2
        l=2
        sum_intake = 0
        for partners in partner:
            data['partner'] = partners.id
            sheet.write(i, 0, partners.name, format2)
            sheet.write(i, 1, "I" , format1)
            sheet.write(t, 0, partners.name, format2)
            sheet.write(t, 1, "T" , format1)
            sheet.col(0).width = int(40*260)
            for obj in self.get_data_from_report(data):
                for emp in obj['data']:
                    col = 2
                    for details in emp['display']:
                        sum_intake += details['months_amount']
                        sheet.write(i, col, str('%.2f' % details['months_amount']), format4)
                        sheet.write(t, col, str('%.2f' % details['months_turnover']), format4)
                        col += 1
                    for total_obj in emp['subtotal_datas']:
                        if emp['partner_id'] == total_obj['partner_id']:
                            sheet.write(t, col, str('%.2f' % total_obj['amount_turn_over']), format4)
                            sheet.write(i, col+1, str('%.2f' % total_obj['amount_totals']), format4)

            i=i+2
            t=t+2
            
        fp = BytesIO()
        workbook.save(fp)
        self.write({'file_name': base64.encodestring(fp.getvalue()), 'move_data':file_name})
        fp.close()
            
        return {
                'name': 'Sale Orders Xls',
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.reports',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'target': 'new',
        }
          


































