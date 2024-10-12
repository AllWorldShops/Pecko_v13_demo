# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict
from odoo import models, fields, api
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer/Customer Name')
    storage_location_id = fields.Char(string='Storage Location', company_dependent=True)
    new_storage_loc = fields.Char(string="Storage Location New")
    # new_storage_loc = fields.Char(string="Storage Location", company_dependent=True)
    project = fields.Char(string='Project')
    production_cell = fields.Char(string="Production Cell")
    order_seq = fields.Char(string="Order Sequence")
    production_type = fields.Selection([('purchase','Purchased'),('manufacture', 'Manufactured')], string="Purchased / Manufactured")
    country_origin = fields.Char("Country of Origin")
    item_text = fields.Char("Item Text")
    customer_part_number = fields.Char('Customer Part Number')

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
 
    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer/Customer Name',related='product_tmpl_id.manufacturer_id',store=True)
    storage_location_id = fields.Char(string='Storage Location',related='product_tmpl_id.storage_location_id')
    project = fields.Char(string='Project',related='product_tmpl_id.project')
    production_cell = fields.Char(string="Production Cell", related='product_tmpl_id.production_cell')
    order_seq = fields.Char(string="Order Sequence", related='product_tmpl_id.order_seq')
    production_type = fields.Selection([('purchase','Purchased'),('manufacture', 'Manufactured')], string="Purchased / Manufactured", related='product_tmpl_id.production_type')
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
    # deadline_date = fields.Datetime("Deadline Date", compute="_compute_quantities")

#     @api.multi
    def write(self, vals):
        rec = super(ProductProduct, self).write(vals)
        if vals.get('manufacturer_id'):
            product_id = self.env['product.product'].search([('id','=',self.id)])
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

            # if seller.date_start and seller.date_start > date:
            #     continue
            # if seller.date_end and seller.date_end < date:
            #     continue
            # if partner_id and seller.partner_id not in [partner_id, partner_id.parent_id]:
            #     continue
            # if quantity is not None and float_compare(quantity_uom_seller, seller.min_qty, precision_digits=precision) == -1:
            #     continue
            # if seller.product_id and seller.product_id != self:
            #     continue

            if not res or res.partner_id == seller.partner_id:
                res |= seller

        return res.sorted('sequence')[:1]

    # @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    # @api.depends_context(
    #     'lot_id', 'owner_id', 'package_id', 'from_date', 'to_date',
    #     'location', 'warehouse',
    # )
    # def _compute_quantities(self):
    #     products = self.filtered(lambda p: p.type != 'service')
    #     res = products._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
    #     for product in products:
    #         product.update(res[product.id])
    #     # Services need to be set with 0.0 for all quantities
    #     services = self - products
    #     services.qty_available = 0.0
    #     services.incoming_qty = 0.0
    #     services.outgoing_qty = 0.0
    #     services.virtual_available = 0.0
    #     services.free_qty = 0.0
    #     services.deadline_date = None

    # def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
    #     domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
    #     domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc
    #     dates_in_the_past = False
    #     # only to_date as to_date will correspond to qty_available
    #     to_date = fields.Datetime.to_datetime(to_date)
    #     if to_date and to_date < fields.Datetime.now():
    #         dates_in_the_past = True

    #     domain_move_in = [('product_id', 'in', self.ids)] + domain_move_in_loc
    #     domain_move_out = [('product_id', 'in', self.ids)] + domain_move_out_loc
    #     if lot_id is not None:
    #         domain_quant += [('lot_id', '=', lot_id)]
    #     if owner_id is not None:
    #         domain_quant += [('owner_id', '=', owner_id)]
    #         domain_move_in += [('restrict_partner_id', '=', owner_id)]
    #         domain_move_out += [('restrict_partner_id', '=', owner_id)]
    #     if package_id is not None:
    #         domain_quant += [('package_id', '=', package_id)]
    #     if dates_in_the_past:
    #         domain_move_in_done = list(domain_move_in)
    #         domain_move_out_done = list(domain_move_out)
    #     if from_date:
    #         date_date_expected_domain_from = [('date', '>=', from_date)]
    #         domain_move_in += date_date_expected_domain_from
    #         domain_move_out += date_date_expected_domain_from
    #     if to_date:
    #         date_date_expected_domain_to = [('date', '<=', to_date)]
    #         domain_move_in += date_date_expected_domain_to
    #         domain_move_out += date_date_expected_domain_to

    #     Move = self.env['stock.move'].with_context(active_test=False)
    #     Quant = self.env['stock.quant'].with_context(active_test=False)
    #     domain_move_in_todo = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_in
    #     domain_move_out_todo = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_out
    #     moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move._read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
    #     # print(moves_in_res, "moves_in_resmoves_in_res--------------")
    #     moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move._read_group(domain_move_out_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
    #     # print([s.id for s in Move.search(domain_move_out_todo)], "domain_move_out_todo============")
    #     out_moves = Move.search(domain_move_out_todo).filtered(lambda move: move.state not in ('done', 'cancel'))
    #     deadline_date = False
    #     if out_moves:
    #         deadline_date = min(out_moves.mapped('date'), default=fields.Datetime.now())
    #     # ss
    #     quants_res = dict((item['product_id'][0], (item['quantity'], item['reserved_quantity'])) for item in Quant._read_group(domain_quant, ['product_id', 'quantity', 'reserved_quantity'], ['product_id'], orderby='id'))
    #     if dates_in_the_past:
    #         # Calculate the moves that were done before now to calculate back in time (as most questions will be recent ones)
    #         domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_in_done
    #         domain_move_out_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_out_done
    #         moves_in_res_past = dict((item['product_id'][0], item['product_qty']) for item in Move._read_group(domain_move_in_done, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
    #         moves_out_res_past = dict((item['product_id'][0], item['product_qty']) for item in Move._read_group(domain_move_out_done, ['product_id', 'product_qty'], ['product_id'], orderby='id'))

    #     res = dict()
    #     for product in self.with_context(prefetch_fields=False):
    #         origin_product_id = product._origin.id
    #         product_id = product.id
    #         if not origin_product_id:
    #             res[product_id] = dict.fromkeys(
    #                 ['qty_available', 'free_qty', 'incoming_qty', 'outgoing_qty', 'virtual_available'],
    #                 0.0,
    #             )
    #             continue
    #         rounding = product.uom_id.rounding
    #         res[product_id] = {}
    #         if dates_in_the_past:
    #             qty_available = quants_res.get(origin_product_id, [0.0])[0] - moves_in_res_past.get(origin_product_id, 0.0) + moves_out_res_past.get(origin_product_id, 0.0)
    #         else:
    #             qty_available = quants_res.get(origin_product_id, [0.0])[0]
    #         reserved_quantity = quants_res.get(origin_product_id, [False, 0.0])[1]
    #         res[product_id]['qty_available'] = float_round(qty_available, precision_rounding=rounding)
    #         res[product_id]['free_qty'] = float_round(qty_available - reserved_quantity, precision_rounding=rounding)
    #         res[product_id]['incoming_qty'] = float_round(moves_in_res.get(origin_product_id, 0.0), precision_rounding=rounding)
    #         res[product_id]['outgoing_qty'] = float_round(moves_out_res.get(origin_product_id, 0.0), precision_rounding=rounding)
    #         res[product_id]['virtual_available'] = float_round(
    #             qty_available + res[product_id]['incoming_qty'] - res[product_id]['outgoing_qty'],
    #             precision_rounding=rounding)
    #         res[product_id]['deadline_date'] = deadline_date if deadline_date else None

    #     return res

class ResCompanyInh(models.Model):
    _inherit = 'res.company'
    
    logo_one = fields.Binary("DO Report Logo")
    logo_two = fields.Binary("PO Report Logo")
    logo_three = fields.Binary("Invoice Report Logo")
    logo_four = fields.Binary("SO Report Logo")

            