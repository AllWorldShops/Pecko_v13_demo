from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
from io import BytesIO
import xlsxwriter
from odoo.tools.image import image_process


class BomConsolidatedReReport(models.Model):
    _name = 'bom.consolidated.report'
    _description = "BOM Consolidated Report"


    bom_id = fields.Many2one('mrp.bom',string="BOM")
    company_id = fields.Many2one('res.company')
    quantity = fields.Float(string="Quantity",default=1)

    # Generate the BOM Consolidated XLSX report
    def action_bom_consolidated_xlsx_report(self):
        if self.quantity <= 0:
            raise ValidationError(_("Quantity must be greater than or equal to 1."))
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self.bom_id.product_tmpl_id.default_code)
        # FORMATS
        format_head = workbook.add_format({
            'bold': True,
            'valign': 'center',
            'font_size': 14,
            'bg_color': '#5F9EA0',
        })

        bom_head = workbook.add_format({
            'bold': True,
            'valign': 'vcenter',
            'font_size': 12,
            'align': 'center',
            'bg_color': '#fce4d6',
            'text_wrap': True,
            'border': 1,
        })

        bom_head_child = workbook.add_format({
            'bold': True,
            'valign': 'vcenter',
            'font_size': 12,
            'align': 'center',
            'bg_color': '#fce4d6',
            'text_wrap': True,
            'border': 1,
        })

        bom_head_bg = workbook.add_format({
            'bold': True,
            'valign': 'vcenter',
            'font_size': 12,
            'align': 'center',
            'bg_color': '#b4e5a2',
            'text_wrap': True,
            'border': 1,
        })


        format_r_bg = workbook.add_format({
            'align': 'right',
            'valign': 'vright',
            'bg_color': '#b4e5a2',
            'border':1,
            'text_wrap': True,
            'num_format': '#,##0.0000'
        })

        format_r_bg_red = workbook.add_format({
            'align': 'right',
            'valign': 'vright',
            'bg_color':'#FF7F7F',
            'border':1,
            'text_wrap': True,
            'num_format': '#,##0.0000'
        })

        format_c = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True,
        })

        format_l = workbook.add_format({
            'align': 'left',
            'valign': 'vleft',
            'border': 1,
            'text_wrap': True,
        })

        format_r = workbook.add_format({
            'align': 'right',
            'valign': 'vright',
            'border': 1,
            'text_wrap': True,
        })

        format_r_digits = workbook.add_format({
            'align': 'right',
            'valign': 'vright',
            'border': 1,
            'text_wrap': True,
            'num_format': '#,##0.0000'
        })

        # amount_format = workbook.add_format({
        #     'num_format': '#,##0.00'
        # })


        # COLUMN WIDTH
        sheet.set_column(0, 0, 28)
        sheet.set_column(1, 1, 40)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 26)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 18)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(10, 10, 15)

        # TABLE HEADER
        sheet.merge_range(0,0,0,1,'Consolidated BOM',bom_head)
        sheet.write(1,0,'Parent Pecko Part Number',bom_head)
        sheet.write(1,1,'Customer Part Number',bom_head)
        sheet.write(1,2,'Description',bom_head)
        sheet.write(1,3,'Quantity',bom_head)
        sheet.merge_range(5, 0, 6, 0, 'S.No', bom_head)
        sheet.merge_range(5, 1, 6, 1, 'Product', bom_head)
        sheet.merge_range(5, 2, 6, 2, 'Part No', bom_head)
        sheet.merge_range(5, 3, 6, 3, 'Description', bom_head)
        sheet.merge_range(5, 4, 6, 4, 'Manufacturer', bom_head)
        sheet.merge_range(5, 5, 6, 5, 'Total Quantity Required', bom_head)
        sheet.merge_range(5, 6, 6, 6, 'UOM', bom_head)
        sheet.merge_range(5, 7, 6, 7, 'Current On hand Quantity', bom_head_bg)
        sheet.merge_range(5, 8, 6, 8, 'Incoming (PO)', bom_head_bg)
        sheet.merge_range(5, 9, 6, 9, 'Outgoing', bom_head_bg)
        sheet.merge_range(5, 10, 6, 10, 'Total', bom_head_bg)

        sheet.write(2,0,self.bom_id.product_tmpl_id.default_code,format_l)
        sheet.write(2,1,self.bom_id.product_tmpl_id.x_studio_field_qr3ai,format_c)
        sheet.write(2,2,self.bom_id.product_tmpl_id.x_studio_field_mHzKJ,format_l)
        sheet.write(2,3,self.quantity,format_r_digits)
        row = 7
        product_qty_dict = {}
        product_data_dict = {}

        for rec in self.bom_id.bom_line_ids:

            mrp_bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id),
                ('company_id', '=', self.company_id.id)
            ], limit=1, order="id asc")

            # IF CHILD BOM EXISTS
            if mrp_bom and mrp_bom.bom_line_ids:

                for rm_rec in mrp_bom.bom_line_ids:

                    product_id = rm_rec.product_id.id

                    # REQUIRED QTY
                    required_qty = (
                        rm_rec.product_qty *
                        self.quantity
                    )

                    # SUM TOTAL
                    if product_id not in product_qty_dict:
                        product_qty_dict[product_id] = required_qty
                    else:
                        product_qty_dict[product_id] += required_qty

                    # STORE PRODUCT DETAILS
                    product_data_dict[product_id] = rm_rec

            # IF NO CHILD BOM EXISTS -> ADD CURRENT PRODUCT
            else:
                product_id = rec.product_id.id
                required_qty = rec.product_qty * self.quantity
                if product_id not in product_qty_dict:
                    product_qty_dict[product_id] = required_qty
                else:
                    product_qty_dict[product_id] += required_qty

                product_data_dict[product_id] = rec

        sno = 0

        for product_id, total_qty in product_qty_dict.items():

            sno += 1

            rm_rec = product_data_dict[product_id]
            sheet.write(row,0,sno,format_c)
            sheet.write(row,1,rm_rec.product_id.default_code,format_l)
            sheet.write(row,2,rm_rec.product_id.name,format_c)
            sheet.write(row,3,rm_rec.product_id.x_studio_field_mHzKJ,format_l)
            sheet.write(row,4,rm_rec.product_id.manufacturer_id.name if rm_rec.product_id.manufacturer_id else '',format_l)

            # FINAL REQUIRED QTY
            rm_qty = total_qty
            sheet.write(row,5,round(rm_qty,4),format_r_digits)
            sheet.write(row,6,rm_rec.product_uom_id.name if rm_rec.product_uom_id else '',format_c)
            sheet.write(row,7,round(rm_rec.product_id.qty_available,4),format_r_bg)
            sheet.write(row,8,round(rm_rec.product_id.incoming_qty,4),format_r_bg)
            sheet.write(row,9,round(rm_rec.product_id.outgoing_qty,4),format_r_bg)
            qty_total = round((rm_rec.product_id.qty_available + rm_rec.product_id.incoming_qty - rm_rec.product_id.outgoing_qty),4)
            # NEGATIVE STOCK HIGHLIGHT
            if qty_total >= 0:
                sheet.write(row,10,qty_total,format_r_bg)
            else:
                sheet.write(row,10,qty_total,format_r_bg_red)

            row += 1
        row = row + 4
        sheet.write(row,0,'Child BOM Details',bom_head_child)
        row = row + 1
        sheet.write(row,0,'S.No',bom_head)
        sheet.write(row,1,'Pecko Part Number',bom_head)
        sheet.write(row,2,'Customer Part Number',bom_head)
        sheet.write(row,3,'Description',bom_head)
        sheet.write(row,4,'Quantity',bom_head)
        row = row + 1
        child_sno = 0
        for rec in self.bom_id.bom_line_ids:
            mrp_bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id),
                ('company_id', '=', self.company_id.id)
            ], limit=1, order="id asc")
            # PRINT ONLY PRODUCTS HAVING BOM
            if mrp_bom and mrp_bom.bom_line_ids:
                child_sno += 1
                sheet.write(row,0,child_sno,format_c)
                sheet.write(row,1,rec.product_id.default_code,format_l)
                sheet.write(row,2,rec.product_id.x_studio_field_qr3ai,format_c)
                sheet.write(row,3,rec.product_id.x_studio_field_mHzKJ,format_l)
                child_qty = self.quantity * rec.product_qty
                sheet.write(row,4,child_qty,format_r_digits)
                row += 1

        # CREATE FILE
        workbook.close()
        output.seek(0)
        file_data = output.getvalue()
        output.close()
        # report_name = f'SOA_{self.date.strftime("%d-%B-%Y")}_{self.partner_id.name}.xlsx'
        report_name = f'Consolidated_BOM_Report.xlsx'

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

    
   