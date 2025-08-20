from odoo import api, fields, models, _
from datetime import datetime, timedelta,date
import time, re, xlwt, base64, math
from io import BytesIO
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP

from odoo.exceptions import ValidationError


class SalesDetailsReport(models.TransientModel):
    _name = 'sales.details.report'
    _description = "Sales Details Report"

    date_from = fields.Date(
        "From", required=True)
    date_to = fields.Date(
        "To", required=True
    )
    partner_id = fields.Many2one('res.partner',string="Customer",required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)

   
    def generate_report(self):
        if self.date_from and self.date_to:
            if self.date_from > date.today() and self.date_from > self.date_to:
                raise ValidationError("The 'From' date cannot be in the future and 'To' date cannot be in the past. ")
            elif self.date_to < self.date_from:
                raise ValidationError("The 'From' date cannot be in the future and 'To' date cannot be in the past. ")
        # Create workbook and styles
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sales Details Report')
        header_style = xlwt.easyxf("font: bold on, height 280; align: horizontal center, vertical center;")
        subheader_style = xlwt.easyxf("font: bold on, height 240; align: horizontal left, vertical center; ")
        filter_style = xlwt.easyxf("font: bold on, height 190; align: horizontal center, vertical center;")
        text_style = xlwt.easyxf("align: horizontal center, vertical center")
        text_right = xlwt.easyxf("align: horizontal right, vertical center")
        # Create a style that forces two decimal places
        decimal_style = xlwt.XFStyle()
        decimal_style.num_format_str = '0.00'
        # Create alignment object
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_RIGHT  # Set horizontal alignment to right

        # Apply the alignment to the style
        decimal_style.alignment = alignment
        left_align = xlwt.easyxf("align: horizontal left, vertical center;")
        tot_style = xlwt.easyxf("font: bold on; align: horizontal center, vertical center;pattern: pattern solid, fore_color gray25;")
        # Combine total_style and decimal_style into one
        combined_total_decimal_style = xlwt.easyxf(
            "font: bold on; align: horizontal right, vertical center; pattern: pattern solid, fore_color gray25;"
        )
        combined_total_decimal_style.num_format_str = '0.00'  # Apply decimal format

        # Ensure date format is consistent
        from_date = self.date_from.strftime('%d-%m-%Y') if self.date_from else 'N/A'
        to_date = self.date_to.strftime('%d-%m-%Y') if self.date_to else 'N/A'

        worksheet.col(0).width = 256 * 10
        worksheet.col(1).width = 256 * 30
        worksheet.col(2).width = 256 * 30
        worksheet.col(3).width = 256 * 30
        worksheet.col(4).width = 256 * 30
        worksheet.col(5).width = 256 * 30
        worksheet.col(6).width = 256 * 50
        worksheet.col(7).width = 256 * 30
        worksheet.col(8).width = 256 * 30
        worksheet.col(9).width = 256 * 30
        worksheet.col(10).width = 256 * 30
        worksheet.col(11).width = 256 * 30
        worksheet.col(12).width = 256 * 30
        worksheet.col(13).width = 256 * 30
        worksheet.col(14).width = 256 * 30

        # Write headers
        report_title = "Sales Details Report"
        worksheet.write_merge(0, 0, 0, 8, report_title, header_style)
        # Write label-value pairs
        worksheet.write(2, 1, "From : ", subheader_style)
        worksheet.write(2, 2, from_date)
        worksheet.write(2, 3, "To : ", subheader_style)
        worksheet.write(2, 4, to_date)
        worksheet.write(3, 1, "Company : ", subheader_style)
        worksheet.write(3, 2, self.company_id.name)
        worksheet.write(3, 3, 'USD Conversion : ', subheader_style)
        worksheet.write(3, 4, '1.3')


        worksheet.write(7, 0, "S.No ", subheader_style)
        worksheet.write(7, 1, "Customer ", subheader_style)
        worksheet.write(7, 2, "SO Number ", subheader_style)
        worksheet.write(7, 3, "MO Number ", subheader_style)
        worksheet.write(7, 4, "DO Number ", subheader_style)
        worksheet.write(7, 5, "Invoice", subheader_style)
        worksheet.write(7, 6, "Product", subheader_style)
        worksheet.write(7, 7, "Sale Price (USD)", subheader_style)
        worksheet.write(7, 8, "Quantity", subheader_style)
        worksheet.write(7, 9, "Total (USD)", subheader_style)
        worksheet.write(7, 10, "Raw Material Cost (USD)", subheader_style)
        row = 8
        sales_order = self.env['sale.order'].sudo().search([
        ('partner_id', '=', self.partner_id.id),
        ('state', 'in', ['sale', 'done']),('create_date','>=',self.date_from.strftime('%Y-%m-%d 00:00:00')),('create_date','<=',self.date_to.strftime('%Y-%m-%d 23:59:59')),('company_id','=',self.company_id.id)],order="partner_id desc")
        sno = 0
        for sale in sales_order:
            # Precompute repetitive info
            mrp = self.env['mrp.production'].sudo().search([
                ('origin', '=', sale.name),
                ('state', '=', 'done')
            ])
            delivery_orders = self.env['stock.picking'].sudo().search([
                ('picking_type_code', '=', 'outgoing'),
                ('sale_id', '=', sale.id),
                ('state', '=', 'done')
            ])
            delivery_names = ", ".join(delivery_orders.mapped('name')) if delivery_orders else ''
            posted_invoices = sale.invoice_ids.filtered(lambda inv: inv.state == 'posted')
            invoice_names = ", ".join(posted_invoices.mapped('name')) if posted_invoices else ''
            mrp_names = ", ".join(mrp.mapped('name')) if mrp else ''

            # Now loop through each order line separately
            
            for line in sale.order_line:
                sno +=1
                worksheet.write(row, 0, sno)
                worksheet.write(row, 1, sale.partner_id.name)
                worksheet.write(row, 2, sale.name)
                worksheet.write(row, 3, mrp_names)
                worksheet.write(row, 4, delivery_names)
                worksheet.write(row, 5, invoice_names)
                product_name = ''
                if line.product_id and line.product_id.display_name:
                    product_name =  '( ' + line.product_id.display_name + ' ) ' + line.product_id.name
                worksheet.write(row, 6, product_name)   # Product name here
                worksheet.write(row, 7, round(line.price_unit,2))
                worksheet.write(row, 8, line.product_uom_qty)
                total = round(line.price_unit,2) * line.product_uom_qty
                worksheet.write(row, 9, total)
                if line.product_id.bom_count >=1:
                    mrp_bom = self.env['mrp.bom'].search([('product_tmpl_id','=',line.product_template_id.id)],limit=1,order="id desc")
                    if mrp_bom:
                        if line.currency_id.id == line.company_id.currency_id.id:
                            worksheet.write(row, 10, mrp_bom.total_bom_cost )
                        else:
                            # currency_total = mrp_bom.total_bom_cost / line.currency_id.inverse_rate
                            currency_total = mrp_bom.total_bom_cost / line.currency_id.inverse_rate
                            worksheet.write(row, 10, round(currency_total,2) )

                row += 1

        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = base64.b64encode(fp.read())
        fp.close()

        report_name = 'Sales Details Report'
        attachment = self.env['ir.attachment'].create({
            'name': f'{report_name}.xls',
            'datas': data,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'web/content/{attachment.id}?download=true',
            'target': 'current',
        }


   # 