from odoo import models, fields, _, api


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

class StockWarehouseOrderpoint(models.Model):
    """ Defines Minimum stock rules. """
    _inherit = "stock.warehouse.orderpoint"
    
    qty_to_order = fields.Float('To Order', compute='_compute_qty_to_order', inverse='_inverse_qty_to_order', search='_search_qty_to_order', digits='Product Unit of Measure')
    
    @api.depends('qty_to_order_manual', 'qty_to_order_computed')
    def _compute_qty_to_order(self):
        for orderpoint in self:
            orderpoint.qty_to_order = orderpoint.qty_to_order_manual if orderpoint.qty_to_order_manual else orderpoint.qty_to_order_computed

    def _inverse_qty_to_order(self):
        for orderpoint in self:
            if orderpoint.trigger == 'auto':
                orderpoint.qty_to_order_manual = 0
            elif not orderpoint.qty_to_order_manual and not orderpoint.qty_to_order:
                orderpoint.qty_to_order = orderpoint.qty_to_order_computed
            elif orderpoint.qty_to_order != orderpoint.qty_to_order_computed:
                orderpoint.qty_to_order_manual = orderpoint.qty_to_order

    # @api.depends('product_id','product_min_qty','product_max_qty','qty_to_order_manual','qty_to_order_computed')
    # def _compute_qty_to_order(self):

    #     for op in self:
    #         if op.qty_to_order_manual:
    #             op.qty_to_order = op.qty_to_order_manual
    #         else:
    #             forecast = op.product_id.virtual_available

    #             in_progress = op._quantity_in_progress().get(op.id, 0.0)

    #             available_qty = forecast + in_progress

    #             if forecast < op.product_min_qty:
    #                 op.qty_to_order = max(
    #                     0.0,
    #                     op.product_max_qty - forecast
    #                 )
    #             else:
    #                 op.qty_to_order = 0.0
    #         print('qty_to_order-----------',op.qty_to_order)
    #     # stop


    @api.depends('product_id','product_min_qty','product_max_qty','qty_to_order_manual', 'qty_to_order_computed')
    def _compute_qty_to_order(self):
        for op in self:
            if op.qty_to_order_manual:
                op.qty_to_order = op.qty_to_order_manual
            else:
                forecast = op.product_id.virtual_available
                in_progress = op._quantity_in_progress().get(op.id, 0.0)
                if forecast + in_progress < op.product_min_qty:
                    op.qty_to_order = op.product_max_qty - forecast - in_progress
                else:
                    op.qty_to_order = 0.0
            print('qty_to_order-----------',op.qty_to_order)