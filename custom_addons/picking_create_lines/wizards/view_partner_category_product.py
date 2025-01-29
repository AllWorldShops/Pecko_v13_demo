from odoo import api, fields, models, _


class ViewPartnerCategoryProduct(models.TransientModel):
    _name = 'view.partner.category.product'
    _description = "View Partner Category Product"

    partner_code_id = fields.Many2one('list.partner.code.report', string="Partner Code",
                                      domain="[('category_code_id','=',category_code_id)]")
    category_code_id = fields.Many2one('list.category.code.report', string="Category Code")

    def partner_category_product_view(self):
        """It then returns the appropriate view action to display the report in the tree view."""
        view_report = self.env['partner.category.product.view.report']
        category_code = self.category_code_id
        partner_code = self.partner_code_id
        return view_report.get_view_product_report_values(category_code, partner_code)

    @api.model
    def _open_category_code(self):
        """ Open the partner category menu"""
        self._values_category_code()
        return {
            "type": "ir.actions.act_window",
            "res_model": "view.partner.category.product",
            "views": [[self.env.ref('picking_create_lines.view_partner_category_product_from_view').id, "form"],
                      [False, "list"]],
            'view_mode': 'form, list',
            "domain": [],
            "name": _("Partner Category Product View Report"),
            "target": "new",
        }

    def _values_category_code(self):
        """Create the partner code and category code to compare with product."""
        self.env.cr.execute("DELETE FROM list_category_code_report")
        self.env.cr.execute("DELETE FROM list_partner_code_report")
        default_code_ids = self.env['product.product'].sudo().search([]).mapped('default_code')
        category_code_data = {}
        for code in default_code_ids:
            if code:
                category_prefix = code[:4]
                partner_code = code[-4:]
                if category_prefix not in category_code_data:
                    category_code_data[category_prefix] = set()
                category_code_data[category_prefix].add(partner_code)
        category_code_data_to_create = [{'name': cat_code} for cat_code in sorted(category_code_data.keys())]
        if category_code_data_to_create:
            category_ids = self.env['list.category.code.report'].sudo().create(category_code_data_to_create)
            partner_code_data_to_create = []
            for cat in category_ids:
                cat_code = cat.name
                partner_codes = category_code_data[cat_code]
                for partner_code in partner_codes:
                    partner_code_data_to_create.append({
                        'name': partner_code,
                        'category_code_id': cat.id,
                    })
            if partner_code_data_to_create:
                self.env['list.partner.code.report'].sudo().create(partner_code_data_to_create)
