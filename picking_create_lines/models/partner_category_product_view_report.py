from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PartnerCategoryProductViewReport(models.Model):
    _name = 'partner.category.product.view.report'
    _description = 'Partner Category Product View Report'

    category_code = fields.Char(string='Product Category Code')
    partner_code = fields.Char(string='Vendor Code')
    name = fields.Char(string='Product Name')
    product_id = fields.Many2one(comodel_name='product.product', string='Product Internal Reference')
    


    def get_view_product_report_values(self, category_code, partner_code):
        """Generate a product report based on the provided category and partner codes."""
        self.env.cr.execute("DELETE FROM partner_category_product_view_report")
        code_prefix = category_code.name
        code_suffix = partner_code.name
        if code_suffix:
            relevant_codes = self.env['product.product'].sudo().search(
                [('default_code', 'ilike', code_prefix + '%')]).filtered(
                lambda rec: rec.default_code.endswith(code_suffix))
            relevant_codes = relevant_codes.filtered(
                lambda rec: rec.default_code[:4] == code_prefix and rec.default_code[-4:] == code_suffix)
        else:
            relevant_codes = self.env['product.product'].sudo().search(
                [('default_code', 'ilike', code_prefix + '%')])
            relevant_codes = relevant_codes.filtered(lambda rec: rec.default_code[:4] == code_prefix)
        result_data = []
        for product in relevant_codes:
            result_data.append({
                'category_code': product.default_code[:4],
                'partner_code': product.default_code[-4:],
                'name': product.name,
                'product_id': product.id
            })
        if result_data:
            self.sudo().create(result_data)
            self.env.cr.execute("DELETE FROM list_category_code_report")
            self.env.cr.execute("DELETE FROM list_partner_code_report")
            return {
                'name': _('Partner Category Product View Report'),
                'res_model': 'partner.category.product.view.report',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree',
                'target': 'current',
            }
        else:
            raise ValidationError("No Records found for the Period")


class ListPartnerCodeReport(models.Model):
    _name = 'list.partner.code.report'
    _description = 'List Partner Code Report'

    name = fields.Char(string='Vendor Code')
    category_code_id = fields.Many2one('list.category.code.report', string="Category Code")


class ListCategoryCodeReport(models.Model):
    _name = 'list.category.code.report'
    _description = 'List Category Code Report'

    name = fields.Char(string='Category Code')
