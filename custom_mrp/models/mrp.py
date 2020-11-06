from odoo import models, fields, api, _

class MrpProduction(models.Model):
    _inherit = 'mrp.production'


    consumed_move_raw_ids = fields.One2many(related='move_raw_ids', string="Consumed Products")
    finished_line_ids = fields.One2many(related='finished_move_line_ids', string="Consumed Products")
    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer Name')
    customer_part_no = fields.Char(string='Part Number')
    description = fields.Char(string='Description')
    project = fields.Char(string='Project')
    
    # MRP 3 Step Location Auto Change
    def step_location_sync(self):     
        location_route =  self.env['stock.location.route'].search([('name','=','PM Warehouse: Pick components, manufacture and then store products (3 steps)')],limit=1)
        for loc_route in location_route:
            for rul in loc_route.rule_ids:
                if rul.location_src_id.complete_name == 'PM-WH/Production Floor':
                    loc_id = self.env['stock.location'].search([('complete_name','=','Virtual Locations/My Company: Production')],limit=1)
                    if loc_id:
                        rul.location_id = loc_id.id
                        
    def _generate_raw_move(self, bom_line, line_data):
        quantity = line_data['qty']
        # alt_op needed for the case when you explode phantom bom and all the lines will be consumed in the operation given by the parent bom line
        alt_op = line_data['parent_line'] and line_data['parent_line'].operation_id.id or False
        if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom':
            return self.env['stock.move']
        if bom_line.product_id.type not in ['product', 'consu']:
            return self.env['stock.move']
        if self.routing_id:
            routing = self.routing_id
        else:
            routing = self.bom_id.routing_id
        if routing and routing.location_id:
            source_location = routing.location_id
        else:
            source_location = self.location_src_id
        original_quantity = (self.product_qty - self.qty_produced) or 1.0
        data = {
            'sequence': bom_line.sequence,
            'name': bom_line.product_id.x_studio_field_mHzKJ,
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
            'bom_line_id': bom_line.id,
            'picking_type_id': self.picking_type_id.id,
            'product_id': bom_line.product_id.id,
            'product_uom_qty': quantity,
            'product_uom': bom_line.product_uom_id.id,
            'location_id': source_location.id,
            'location_dest_id': self.product_id.property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': bom_line.operation_id.id or alt_op,
            'price_unit': bom_line.product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self.name,
            'warehouse_id': source_location.get_warehouse().id,
            'group_id': self.procurement_group_id.id,
            'propagate': self.propagate,
            'unit_factor': quantity / original_quantity,
            'manufacturer_id': bom_line.product_id.manufacturer_id.id,
            'customer_part_no': bom_line.product_id.name
        }
        return self.env['stock.move'].create(data)
    
    @api.onchange('product_id')
    def onchange_mrp_product(self):
        for mrp_product in self:
            if mrp_product.product_id:
                mrp_product.manufacturer_id = mrp_product.product_id.product_tmpl_id.manufacturer_id
                mrp_product.customer_part_no = mrp_product.product_id.name
                mrp_product.description = mrp_product.product_id.product_tmpl_id.x_studio_field_mHzKJ
    
    @api.model
    def create(self, vals):
        product_id = self.env['product.product'].search([('id','=',vals['product_id'])])
        vals['manufacturer_id'] = product_id.product_tmpl_id.manufacturer_id.id
        vals['customer_part_no'] = product_id.name
        vals['description'] = product_id.product_tmpl_id.x_studio_field_mHzKJ
        return super(MrpProduction, self).create(vals)
          
class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    
    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer')
    customer_part_no = fields.Text(string='Part Number',compute="_compute_product_name",store=True)
    
    @api.depends('product_id')
    def _compute_product_name(self):
        for pro in self:
            if pro.product_id:
                pro.customer_part_no = pro.product_id.name
            else:
                pro.customer_part_no = ''

    @api.onchange('product_id')
    def onchange_mrp_product(self):
        if self.product_id:
            self.manufacturer_id = self.product_id.manufacturer_id
            self.x_studio_field_gVfQK = self.product_id.product_tmpl_id.x_studio_field_mHzKJ
    
class StockMove(models.Model):
    _inherit = 'stock.move'
    
    storage_location_id = fields.Char(string='Storage Location')
    to_consume_qty = fields.Float(string="To Consume Quantity", compute='_get_consumed_data')
    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer Name')
    customer_part_no = fields.Text(string='Part Number',compute="_compute_product_name",store=True)
    
    @api.depends('product_id')
    def _compute_product_name(self):
        for pro in self:
            if pro.product_id:
                pro.customer_part_no = pro.product_id.name
            else:
                pro.customer_part_no = ''
                
    @api.model
    def create(self, vals):
        product_id = self.env['product.product'].search([('id','=',vals['product_id'])])
        vals['storage_location_id'] = product_id.product_tmpl_id.storage_location_id
        vals['manufacturer_id'] = product_id.product_tmpl_id.manufacturer_id.id
        vals['description_picking'] = product_id.product_tmpl_id.x_studio_field_mHzKJ
        
        if product_id.product_tmpl_id.x_studio_field_mHzKJ:
            vals['name'] = product_id.product_tmpl_id.x_studio_field_mHzKJ
        else:
            if vals.get('sale_line_id'):
                sale_line_id = self.env['sale.order.line'].search([('id','=',vals.get('sale_line_id'))])
                vals['name'] = sale_line_id.name
            if vals.get('purchase_line_id'):
                purchase_line_id = self.env['purchase.order.line'].search([('id','=',vals.get('purchase_line_id'))])
                vals['name'] = purchase_line_id.name
        return super(StockMove, self).create(vals)
    
    @api.depends('product_uom_qty')
    def _get_consumed_data(self):
        for rec in self:
            rec.to_consume_qty = rec.product_uom_qty - rec.quantity_done

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    qty_to_produce = fields.Float(compute='_to_produce_qty', string="Quantity To Produce")

    @api.depends('move_id')
    def _to_produce_qty(self):
        for rec in self:
            rec.qty_to_produce = rec.move_id.product_uom_qty - rec.qty_done