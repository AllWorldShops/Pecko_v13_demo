from odoo import models, fields, api, _
from odoo import tools, api
from odoo.exceptions import UserError, ValidationError
import base64
from odoo.http import request
from io import BytesIO
import xlsxwriter
from odoo.tools.image import image_process


class PartnerInvoiceStatement(models.TransientModel):
    _name = 'partner.invoice.statement'
    _description = 'Partner Invoice Statement'

    date = fields.Date(string="AS On Date")
    partner_id = fields.Many2one('res.partner',string="Partner")
    company_id = fields.Many2one('res.company',string="Company")


    # Generate the partner overdue statement report 11-05-2026
    def action_partner_statement_report_xlsx(self):
        # # Create an in-memory BytesIO stream
        output = BytesIO()
        # # Create the workbook and worksheet
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self.partner_id.name)
        # # # Define formats
        format_head = workbook.add_format({
            'bold': True, 'valign': 'center','font_size': 14,'bg_color':'#5F9EA0',
        })

        prod_head = workbook.add_format({
            'bold': True,'valign': 'vcenter','font_size': 12,'align': 'center','bg_color':'#fce4d6','text_wrap': True,
        })
        prod_head_pt = workbook.add_format({
            'bold': True,'valign': 'vleft','font_size': 12,'align': 'center','text_wrap':True
        })

        acc_head = workbook.add_format({
            'bold': True,
            'font_size': 13,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'bg_color':'#D3D3D3'
        })
        company_name = workbook.add_format({
            'font_size': 11,
            'align': 'left',
            'valign': 'top',
            'text_wrap': True,
        })
        company_name_head = workbook.add_format({
            'font_size': 14,
            'align': 'left',
            'valign': 'top',
            'text_wrap': True,
        })


        due = workbook.add_format({
            'font_size': 12,
            'align': 'left',
            'font_color':'red'

        })

        format_c = workbook.add_format({'align': 'center','valign': 'center',})

        if self.company_id.logo:
            source = base64.b64decode(self.company_id.logo)
            image_data = BytesIO(image_process(source, size=(100, 100)))
            # Insert image
            sheet.set_row(0, 34) 
            sheet.set_column(0, 40)   # Column A width = 25
            sheet.insert_image(0, 0, "company.png", {
                "image_data": image_data,
                "x_scale": 1.6,
                "y_scale": 1,
            })

        # Formats
        company_name_head = workbook.add_format({
            'bold': True,
            'font_size': 16,
        })

        company_name = workbook.add_format({
            'font_size': 11,
            'text_wrap': True,
            'valign': 'top',
        })
        sheet.merge_range(1, 0, 1, 3, '', company_name)
        as_at_date = "AS AT " + str(self.date.strftime('%d-%m-%Y'))

        text = f"STATEMENT OF ACCOUNTS\n{as_at_date}"

        sheet.merge_range(2, 0, 3, 9, text, acc_head)
        sheet.write_rich_string(
            1, 0,

            company_name_head,
            f"{self.company_id.name or ''}\n",

            company_name,

            f"{self.company_id.street or ''}, "
            f"{self.company_id.street2 or ''}, "
            f"{self.company_id.city or ''} "
            f"{self.company_id.zip or ''}\n"

            f"Ph: {self.company_id.phone or ''} "
            f"Fax: {self.company_id.fax or ''}\n"

            f"Email: {self.company_id.email or ''}, "
            f"URL: {self.company_id.website or ''}\n"

            f"GST REG NO. : {self.company_id.vat or ''}"
        )

        company_name_partner = workbook.add_format({
            'bold': True,
            'font_size': 12,
        })
        partner_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'font_size': 11,
        })
        amount_format = workbook.add_format({
            'num_format': '#,##0.000'
        })
        sheet.merge_range(4, 0, 4, 3, '', partner_format)
        sheet.write_rich_string(
            4, 0,

            company_name_partner,
            f"{self.partner_id.name or ''}\n",

            partner_format,

            f"{self.partner_id.street or ''}\n"
            f"{self.partner_id.street2 or ''}\n"
            f"{self.partner_id.city or ''} "
            f"{self.partner_id.zip or ''}"
        )
        sheet.set_column(0, 0, 10)
        sheet.set_column(1, 1, 25)
        sheet.set_column(2, 2, 17)
        sheet.set_column(3, 3, 17)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 10)
        sheet.set_column(6, 6, 18)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 20)        
        sheet.write(5,8, 'Payment Terms :',prod_head_pt)
        sheet.merge_range(6, 0, 7, 0, 'S.No', prod_head)
        sheet.merge_range(6, 1, 7, 1, 'Invoice No', prod_head)
        sheet.merge_range(6, 2, 7, 2, 'Date',prod_head)
        sheet.merge_range(6, 3, 7, 3, 'Due Date',prod_head)
        sheet.merge_range(6, 4, 7, 4, 'Customer Po No.',prod_head)
        sheet.merge_range(6, 5, 7, 5,'Currency',prod_head)
        sheet.merge_range(6, 6, 7, 6, 'Original Amount',prod_head)
        sheet.merge_range(6, 7, 7, 7, 'Amount Received',prod_head)
        sheet.merge_range(6, 8, 7, 8, 'Balance Due',prod_head)
        sheet.merge_range(6, 9, 7, 9, 'Running Total',prod_head)
        row = 8
        sno = 0
        # h_sno = 0
        account_move = self.env['account.move'].search([('partner_id','=',self.partner_id.id),('state','=','posted'),('move_type','=','out_invoice'),('invoice_date','<=',self.date),('company_id','=',self.company_id.id),('amount_residual','>',0)],order="id asc")
        sheet.write(5,9, account_move[0].invoice_payment_term_id.name if account_move[0].invoice_payment_term_id else '',prod_head_pt)
        running_total = 0
        for rec in account_move:
            sno+=1
            sheet.write(row,0, sno,format_c)
            sheet.write(row,1, rec.name)
            sheet.write(row,2, rec.invoice_date.strftime('%d-%m-%Y'))
            sheet.write(row,3, rec.invoice_date_due.strftime('%d-%m-%Y'))
            sheet.write(row,4, rec.customer_po_no)
            sheet.write(row,5, rec.currency_id.name if rec.currency_id else '')
            sheet.write(row,6, rec.amount_total_in_currency_signed,amount_format)
            total_paid = rec.amount_total_in_currency_signed - rec.amount_residual
            sheet.write(row,7, total_paid,amount_format)
            sheet.write(row,8, rec.amount_residual,amount_format)
            running_total +=rec.amount_residual
            sheet.write(row,9, running_total,amount_format)
            if rec.invoice_date_due < self.date:
                sheet.write(row,10, 'DUE',due)
            row +=1
        # Close the workbook
        workbook.close()
        # Save the workbook in the BytesIO stream
        output.seek(0)
        file_data = output.getvalue()
        output.close()
        report_name = f'SOA_{self.date.strftime("%d-%B-%Y")}_{self.partner_id.name}.xlsx'
        # Create an attachment in Odoo
        attach_id = self.env['ir.attachment'].sudo().create({
            'name': report_name,
            'type': 'binary',
            'public': True,
            'datas': base64.b64encode(file_data),
        })

        # Generate the URL for download
        url = f"/web/content/?model=ir.attachment&id={attach_id.id}&filename_field=name&field=datas&download=true&"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

   