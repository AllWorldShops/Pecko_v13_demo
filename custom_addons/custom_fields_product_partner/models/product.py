from odoo import models, fields
from odoo import SUPERUSER_ID, _, api, fields, models


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

class StockWarehouseOrderpoint(models.Model):
    """ Defines Minimum stock rules. """
    _inherit = "stock.warehouse.orderpoint"
    
    qty_to_order = fields.Float('To Order', compute='_compute_qty_to_order', inverse='_inverse_qty_to_order', search='_search_qty_to_order', digits='Product Unit of Measure')

    # As per Suresh request, we have updated the qty_to_order value to address the issue where MO was not being triggered 
    # during SO confirmation or while running the Reordering Rule. The root cause was that the Reordering Rule was not updating the 'To Order' quantity correctly. 
    # To resolve this, we modified the default flow logic accordingly.
    @api.depends('product_id','product_min_qty','product_max_qty','qty_to_order_manual', 'qty_to_order_computed')
    def _compute_qty_to_order(self):
        for op in self:
            forecast = op.product_id.virtual_available
            if forecast < op.product_min_qty:
                op.qty_to_order = op.product_max_qty - forecast
            else:
                op.qty_to_order = 0.0
        # for orderpoint in self:
        #     orderpoint.qty_to_order = orderpoint.qty_to_order_manual if orderpoint.qty_to_order_manual else orderpoint.qty_to_order_computed