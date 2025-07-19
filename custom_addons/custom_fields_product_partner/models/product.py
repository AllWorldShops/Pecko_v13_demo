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

    def button_plan(self):

        orderpoints = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', 100280)])
        ss = orderpoints._compute_qty_to_order()
        print('---------',ss)


        # filtered_products = []
        # product = self.env['product.product'].browse(100280)
        # orderpoints = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', product.id)])
        # # for op in orderpoints:
        # #     if op.virtual_available < op.product_min_qty:
        # if orderpoints:
        #     filtered_products.append(product.id)
        # if filtered_products:
        #     wizard = self.env['product.replenish'].create({
        #         'product_id': product.id,
        #         'product_tmpl_id': product.product_tmpl_id.id,
        #         'product_uom_id': product.uom_id.id,
        #         'route_id': 6,
        #     })
        #     # wizard.launch_replenishment()
        #     wizard.action_replenish()

        # product = self.env['product.product'].browse(100280)
        # orderpoints = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', product.id)])
        # self.env['stock.warehouse.orderpoint']._run_manually(product_ids=product.ids,location_id=None)
        # for op in self.env['stock.warehouse.orderpoint'].search([('product_id', '=', 100280)]):
        #     if product.virtual_available < op.product_min_qty:
        #         op._generate_replenishment()
        self.env['stock.warehouse.orderpoint']._procure_orderpoint_confirm()

        # for op in orderpoints:
        #     forecast = product.virtual_available
        #     print("Forecast for %s: %s", product.name, forecast)
        #     print("Min Qty: %s", op.product_min_qty)
        #     print("Max Qty: %s", op.product_max_qty)

        #     if forecast < op.product_min_qty:
        #         print("Product %s should trigger reorder!", product.name)
        #     else:
        #         print("Product %s does NOT need reorder (forecast >= min)", product.name)

        # product = self.env['product.product'].browse(100280)
        # location = self.env.ref('stock.stock_location_stock')  # internal location

        # self.env['stock.rule']._run(product=product,qty=10,location_id=location,values={})
        # product = self.env['product.product'].browse(100280)
        # orderpoints = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', product.id)])
        # product._compute_quantities()
        # self.env['procurement.group'].sudo().run_scheduler()
        # orderpoints._compute_stock()
        # self.env['stock.warehouse.orderpoint']._run_auto_orderpoint(orderpoints)
        # orderpoints._run_auto_orderpoint(orderpoints)


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

    @api.depends('product_id','product_min_qty','product_max_qty','qty_to_order_manual', 'qty_to_order_computed')
    def _compute_qty_to_order(self):
        for op in self:
            forecast = op.product_id.virtual_available
            # As per Suresh request, we have updated the qty_to_order value to address the issue where MO was not being triggered 
            # during SO confirmation or while running the Reordering Rule. The root cause was that the Reordering Rule was not updating the 'To Order' quantity correctly. 
            # To resolve this, we modified the default flow logic accordingly.
            if forecast < op.product_min_qty:
                op.qty_to_order = op.product_max_qty - forecast
            else:
                op.qty_to_order = 0.0
        # for orderpoint in self:
        #     orderpoint.qty_to_order = orderpoint.qty_to_order_manual if orderpoint.qty_to_order_manual else orderpoint.qty_to_order_computed