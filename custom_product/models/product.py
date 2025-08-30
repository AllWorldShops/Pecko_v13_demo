# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    manufacturer_id = fields.Many2one('product.manufacturer', string='Manufacturer/Customer Name')
    storage_location_id = fields.Char(string='Storage Location', company_dependent=True)
    new_storage_loc = fields.Char(string="Storage Location New")
    project = fields.Char(string='Project')
    production_cell = fields.Char(string="Production Cell")
    customer_goods = fields.Char(string="Customer Goods Description")
    tariff_code = fields.Char(string="Tariff Code")
    tariff_unit = fields.Char(string="Tariff Unit")
    import_duty_rate = fields.Char(string="Import Duty Rate")
    eksport_duty_rate = fields.Char(string="Eksport Duty Rate")
    sst = fields.Char(string="SST")
    order_seq = fields.Char(string="Order Sequence")
    production_type = fields.Selection([('purchase', 'Purchased'), ('manufacture', 'Manufactured')],
                                       string="Purchased / Manufactured")
    country_origin = fields.Char("Country of Origin")
    item_text = fields.Char("Item Text")
    customer_part_number = fields.Char('Customer Part Number')
    classification_code_name = fields.Char('Code Name')
    classification_code_id = fields.Many2one('classification.code', string='Code Name')
    standard_price = fields.Float(
        'Cost', compute='_compute_standard_price',
        inverse='_set_standard_price', search='_search_standard_price',
        digits='Cost Price',
        groups="base.group_user",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
        In FIFO: value of the last unit that left the stock (automatically computed).
        Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
        Used to compute margins on sale orders.""")



class ProductProduct(models.Model):
    _inherit = 'product.product'

    manufacturer_id = fields.Many2one('product.manufacturer', string='Manufacturer/Customer Name',
                                      related='product_tmpl_id.manufacturer_id', store=True)
    storage_location_id = fields.Char(string='Storage Location', related='product_tmpl_id.storage_location_id')
    project = fields.Char(string='Project', related='product_tmpl_id.project')
    production_cell = fields.Char(string="Production Cell", related='product_tmpl_id.production_cell')
    order_seq = fields.Char(string="Order Sequence", related='product_tmpl_id.order_seq')
    production_type = fields.Selection([('purchase', 'Purchased'), ('manufacture', 'Manufactured')],
                                       string="Purchased / Manufactured", related='product_tmpl_id.production_type')
    country_origin = fields.Char("Country of Origin", related='product_tmpl_id.country_origin', readonly=False)
    item_text = fields.Char("Item Text", related='product_tmpl_id.item_text')
    customer_part_number = fields.Char('Customer Part Number')
    standard_price = fields.Float(
        'Cost', company_dependent=True,
        digits='Cost Price',
        groups="base.group_user",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
        In FIFO: value of the last unit that left the stock (automatically computed).
        Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
        Used to compute margins on sale orders.""")

    def write(self, vals):
        rec = super(ProductProduct, self).write(vals)
        if vals.get('manufacturer_id'):
            product_id = self.env['product.product'].search([('id', '=', self.id)])
            product_id.product_tmpl_id.manufacturer_id = vals.get('manufacturer_id')
        return rec

    def _select_seller(self, partner_id=False, quantity=0.0, date=None, uom_id=False, params=False):
        self.ensure_one()
        if date is None:
            date = fields.Date.context_today(self)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        res = self.env['product.supplierinfo']
        sellers = self._prepare_sellers(params)
        sellers = sellers.filtered(lambda s: not s.company_id or s.company_id.id == self.env.company.id)
        for seller in sellers:
            # Set quantity in UoM of seller
            quantity_uom_seller = quantity
            if quantity_uom_seller and uom_id and uom_id != seller.product_uom:
                quantity_uom_seller = uom_id._compute_quantity(quantity_uom_seller, seller.product_uom)
            if not res or res.partner_id == seller.partner_id:
                res |= seller

        return res.sorted('sequence')[:1]


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    total_amount = fields.Monetary(
        string='Total',
        compute='_compute_total_amount',
        currency_field='currency_id',
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    @api.depends('product_line_ids.subtotal')
    def _compute_total_amount(self):
        for request in self:
            request.total_amount = sum(request.product_line_ids.mapped('subtotal'))


class ApprovalProductLine(models.Model):
    _inherit = 'approval.product.line'

    part_number = fields.Char(string='Part Number', related='product_id.name')
    # manufacturer = fields.Many2one('res.partner', string='Manufacturer', related='product_id.manufacturer_id',
    #                                store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='product_id.currency_id', store=True)
    unit_price = fields.Float(string='Unit Price', related='product_id.list_price', store=True)
    subtotal = fields.Monetary(string='Sub Total', compute='_compute_subtotal', currency_field='currency_id',
                               store=True)

    @api.depends('unit_price', 'quantity')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.unit_price * line.quantity


class ResCompanyInh(models.Model):
    _inherit = 'res.company'

    logo_one = fields.Binary("DO Report Logo")
    logo_two = fields.Binary("PO Report Logo")
    logo_three = fields.Binary("Invoice Report Logo")
    logo_four = fields.Binary("SO Report Logo")
    logo_qa_passed = fields.Binary("QA Passed")
    inspected_by = fields.Char(string='Inspected By')
    approved_by = fields.Char(string='Approved By')
    is_coc_report = fields.Boolean(string='Is COC Report')
    business_reg_no = fields.Char(string='Business Registration No')
    misc_code = fields.Char(string='MISC Code')
    business_des = fields.Char(string='Business Activity Description')


class IdType(models.Model):
    _name = 'id.type'
    _description = 'ID Type'

    id_name = fields.Char(string='Name')
    name = fields.Char(string='Name')


class ClassificationCode(models.Model):
    _name = 'classification.code'
    _description = 'ClassificationCode'
    _rec_name = 'code'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
