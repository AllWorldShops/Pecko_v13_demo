from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
from io import BytesIO
import xlsxwriter
from odoo.tools.image import image_process


class PartnerInvoiceStatement(models.TransientModel):
    _name = 'partner.invoice.statement'
    _description = 'Partner Invoice Statement'

    date = fields.Date(string="AS On Date")
    partner_id = fields.Many2one('res.partner', string="Partner")
    company_id = fields.Many2one('res.company', string="Company")

    # Generate the partner overdue statement report
    def action_partner_statement_report_xlsx(self):

        output = BytesIO()

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self.partner_id.name)
        # FORMATS
        format_head = workbook.add_format({
            'bold': True,
            'valign': 'center',
            'font_size': 14,
            'bg_color': '#5F9EA0',
        })

        prod_head = workbook.add_format({
            'bold': True,
            'valign': 'vcenter',
            'font_size': 13,
            'align': 'center',
            'bg_color': '#fce4d6',
            'text_wrap': True,
            # 'border': 1,
        })

        prod_head_pt = workbook.add_format({
            'bold': True,
            'valign': 'vcenter',
            'font_size': 12,
            'align': 'center',
            'text_wrap': True
        })

        acc_head = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'bg_color': '#D3D3D3',
            # 'border': 1,
        })

        company_name_head = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'left',
            'valign': 'top',
        })

        company_name = workbook.add_format({
            'font_size': 11,
            'text_wrap': True,
            'valign': 'top',
            'align': 'left',
        })

        company_name_partner = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'left',
            'valign': 'top',
        })

        partner_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'align': 'left',
            'font_size': 11,
        })

        due = workbook.add_format({
            'font_size': 12,
            'align': 'left',
            'font_color': 'red'
        })

        format_c = workbook.add_format({
            'align': 'center',
            'valign': 'center',
        })

        amount_format = workbook.add_format({
            'num_format': '#,##0.00'
        })

        # COLUMN WIDTH
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

        # LOGO
        if self.company_id.logo:

            source = base64.b64decode(self.company_id.logo)

            image_data = BytesIO(
                image_process(source, size=(100, 90))
            )

            # Proper row height for logo
            sheet.set_row(0, 35)

            # Prevent overlap
            sheet.merge_range(0, 0, 0, 1, '', workbook.add_format())

            sheet.insert_image(
                0,
                0,
                "company.png",
                {
                    "image_data": image_data,

                    # Stable scaling for live server
                    "x_scale": 1,
                    "y_scale": 1,

                    # Better alignment
                    "x_offset": 5,
                    "y_offset": 2,

                    # Prevent auto movement/stretch
                    "object_position": 1,
                }
            )

        # COMPANY ADDRESS
        company_text = (
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

        sheet.merge_range(1, 0, 4, 3, '', company_name)

        sheet.set_row(1, 22)
        sheet.set_row(2, 22)
        sheet.set_row(3, 22)
        sheet.set_row(4, 22)

        sheet.write_rich_string(
            1, 0,

            company_name_head,
            f"{self.company_id.name or ''}\n",

            company_name,
            company_text
        )

        # STATEMENT HEADER
        as_at_date = "AS AT " + str(self.date.strftime('%d-%m-%Y'))
        text = f"STATEMENT OF ACCOUNTS\n{as_at_date}"
        sheet.merge_range(5, 0, 6, 9, text, acc_head)
        sheet.set_row(5, 18)
        sheet.set_row(6, 18)

        # PARTNER ADDRESS
        partner_text = (
            f"{self.partner_id.street or ''}\n"
            f"{self.partner_id.street2 or ''}\n"
            f"{self.partner_id.city or ''} "
            f"{self.partner_id.zip or ''}"
        )

        sheet.merge_range(7, 0, 9, 3, '', partner_format)
        sheet.set_row(7, 22)
        sheet.set_row(8, 22)
        sheet.set_row(9, 22)
        sheet.write_rich_string(
            7, 0,

            company_name_partner,
            f"{self.partner_id.name or ''}\n",

            partner_format,
            partner_text
        )

        # ACCOUNT MOVE DATA
        account_move = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '<=', self.date),
            ('company_id', '=', self.company_id.id),
            ('amount_residual', '>', 0)
        ], order="id asc")

        if len(account_move) == 0:
            raise ValidationError(_("No Record Found for - %s") % (self.partner_id.name))

        # PAYMENT TERMS
        sheet.write(9, 8, 'Payment Terms :', prod_head_pt)

        if account_move and account_move[0].invoice_payment_term_id:
            sheet.write(
                9,
                9,
                account_move[0].invoice_payment_term_id.name,
                prod_head_pt
            )

        # TABLE HEADER
        sheet.merge_range(10, 0, 11, 0, 'S.No', prod_head)
        sheet.merge_range(10, 1, 11, 1, 'Invoice No', prod_head)
        sheet.merge_range(10, 2, 11, 2, 'Date', prod_head)
        sheet.merge_range(10, 3, 11, 3, 'Due Date', prod_head)
        sheet.merge_range(10, 4, 11, 4, 'Customer Po No.', prod_head)
        sheet.merge_range(10, 5, 11, 5, 'Currency', prod_head)
        sheet.merge_range(10, 6, 11, 6, 'Original Amount', prod_head)
        sheet.merge_range(10, 7, 11, 7, 'Amount Received', prod_head)
        sheet.merge_range(10, 8, 11, 8, 'Balance Due', prod_head)
        sheet.merge_range(10, 9, 11, 9, 'Running Total', prod_head)

        row = 12
        sno = 0
        running_total = 0
        for rec in account_move:
            sno += 1
            sheet.write(row, 0, sno, format_c)
            sheet.write(row, 1, rec.name)
            sheet.write(row, 2, rec.invoice_date.strftime('%d-%m-%Y'))
            sheet.write(row, 3, rec.invoice_date_due.strftime('%d-%m-%Y'))
            sheet.write(row, 4, rec.customer_po_no)
            sheet.write(row, 5, rec.currency_id.name if rec.currency_id else '')
            sheet.write(row, 6, rec.amount_total_in_currency_signed, amount_format)

            total_paid = rec.amount_total_in_currency_signed - rec.amount_residual

            sheet.write(row, 7, total_paid, amount_format)
            sheet.write(row, 8, rec.amount_residual, amount_format)

            running_total += rec.amount_residual

            sheet.write(row, 9, running_total, amount_format)

            if rec.invoice_date_due < self.date:
                sheet.write(row, 10, 'DUE', due)

            row += 1

        # CREATE FILE
        workbook.close()
        output.seek(0)
        file_data = output.getvalue()
        output.close()
        report_name = f'SOA_{self.date.strftime("%d-%B-%Y")}_{self.partner_id.name}.xlsx'

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