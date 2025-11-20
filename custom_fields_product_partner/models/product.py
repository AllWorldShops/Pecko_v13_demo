from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    activity_date_deadline = fields.Datetime('Next Activity Deadline', readonly=False)
    message_last_post = fields.Datetime('Last Message Date')
    x_studio_field_E1WLc = fields.Boolean('')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    quote_description = fields.Html('Description for the quote')
    activity_date_deadline = fields.Datetime('Next Activity Deadline', readonly=False)
    message_last_post = fields.Datetime('Last Message Date')
    x_studio_field_CPhNY = fields.Many2one('x_itemgroup', string='Item Group')
    x_studio_field_TVZyx = fields.Integer('')
    x_studio_field_jXS3W = fields.Many2one('uom.uom', string='Sale Unit of Measure - Reference ONLY')
    x_studio_field_qr3ai = fields.Char('MPN/Customer/Supplier Part No')
    x_studio_field_pFxVK = fields.Char('Customer | Supplier Part Number (Search Key 1)')
    x_studio_field_mHzKJ = fields.Char('Description')


class Manufacturer(models.Model):
    _name = 'x_manufacturer'
    _description = 'Manufacturer'

    x_name = fields.Char('Name')


class ItemGroup(models.Model):
    _name = 'x_itemgroup'
    _description = 'Item Group'

    x_name = fields.Char('Name')


class UoM(models.Model):
    _inherit = 'uom.uom'

    x_studio_field_CBfr8 = fields.Char('Description')

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    customer_part_number = fields.Char(string='Customer Part Number', related='product_tmpl_id.x_studio_field_qr3ai')