from email.policy import default
from odoo import models, fields, api, _
from odoo.tools import float_round

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    consumed_move_raw_ids = fields.One2many(related='move_raw_ids', string="Consumed Products")
    finished_line_ids = fields.One2many(related='finished_move_line_ids', string="Consumed Products")
    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer Name')
    customer_part_no = fields.Char(string='Part Number')
    description = fields.Char(string='Description')
    # project = fields.Char(string='Project')
    project = fields.Char(string='Project',related='product_tmpl_id.project', store=True)
    start_date = fields.Date('Start Date P2')
    start_date_one = fields.Date('Start Date P1')
    order_seq = fields.Char(string='Order Sequence')
    production_cell = fields.Char(string='Production Cell',related='product_tmpl_id.production_cell', store=True)
    reserved = fields.Boolean("Reserved Compute", compute="_compute_reserved")
    reserved_check = fields.Boolean("Reserved", default=False)
    
    def _compute_reserved(self):
        reserved_qty = []
        wo_flag = self.env['ir.config_parameter'].sudo().get_param(
                    'custom_mrp.workorder_flag')

        for line in self.move_raw_ids:
            reserved_qty.append(line.reserved_availability)
        for rec in self:
            if 0 in reserved_qty and wo_flag:
                rec.reserved = True
                rec.reserved_check = rec.reserved
            else:
                rec.reserved = False
                rec.reserved_check = False
    
    @api.onchange('product_id')
    def onchange_responsible(self):
        if self.product_id:
            self.user_id = self.product_id.responsible_id.id
            # self.order_seq = self.product_id.order_seq or ' '
            
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
    item_text = fields.Char("Item Text", related='product_id.item_text')

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
    
    storage_location_id = fields.Char(string='Storage Location', company_dependent=True,store=True)
    to_consume_qty = fields.Float(string="To Consume Quantity", compute='_get_consumed_data')
    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer Name')
    customer_part_no = fields.Text(string='Part Number',compute="_compute_product_name",store=True)
    item_text = fields.Char("Item Text", related='product_id.item_text')

    # def _compute_storage_location_id(self):
    #     ir_property = self.env['ir.property'].browse()
        
    #     for line in self:
    
    @api.depends('product_id')
    def _compute_product_name(self):
        for pro in self:
            if pro.product_id:
                pro.customer_part_no = pro.product_id.name
            else:
                pro.customer_part_no = ' '
                
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

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrderInherit, self).action_confirm()
        mrp = self.env['mrp.production'].search([('origin', '=', self.name)])
        if mrp:
            for line in mrp:
                line.user_id = line.product_id.responsible_id.id or False
        return res
    
class ReportBomStructureInherit(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure' 
    
    
    def _get_bom(self, bom_id=False, product_id=False, line_qty=False, line_id=False, level=False):
        bom = self.env['mrp.bom'].browse(bom_id)
        company = bom.company_id or self.env.company
        bom_quantity = line_qty
        
        if line_id:
            current_line = self.env['mrp.bom.line'].browse(int(line_id))
            bom_quantity = current_line.product_uom_id._compute_quantity(line_qty, bom.product_uom_id) or 0
        # Display bom components for current selected product variant
        if product_id:
            product = self.env['product.product'].browse(int(product_id))
        else:
            product = bom.product_id or bom.product_tmpl_id.product_variant_id
        if product:
            price = product.uom_id._compute_price(product.with_context(force_company=company.id).standard_price, bom.product_uom_id) * bom_quantity
            attachments = self.env['mrp.document'].search(['|', '&', ('res_model', '=', 'product.product'),
            ('res_id', '=', product.id), '&', ('res_model', '=', 'product.template'), ('res_id', '=', product.product_tmpl_id.id)])
        else:
            # Use the product template instead of the variant
            price = bom.product_tmpl_id.uom_id._compute_price(bom.product_tmpl_id.with_context(force_company=company.id).standard_price, bom.product_uom_id) * bom_quantity
            attachments = self.env['mrp.document'].search([('res_model', '=', 'product.template'), ('res_id', '=', bom.product_tmpl_id.id)])
        operations = []
        if bom.product_qty > 0:
            operations = self._get_operation_line(bom.routing_id, float_round(bom_quantity / bom.product_qty, precision_rounding=1, rounding_method='UP'), 0)
        lines = {
            'bom': bom,
            'bom_qty': bom_quantity,
            'company_id': bom.company_id,
            'bom_prod_name': product.display_name,
            'currency': company.currency_id,
            'product': product,
            'code': bom and bom.display_name or '',
            'price': price,
            'total': sum([op['total'] for op in operations]),
            'level': level or 0,
            'operations': operations,
            'operations_cost': sum([op['total'] for op in operations]),
            'attachments': attachments,
            'operations_time': sum([op['duration_expected'] for op in operations])
            }
        components, total = self._get_bom_lines(bom, bom_quantity, product, line_id, level)
        lines['components'] = components
        lines['total'] += total
        return lines 
    
    
    def _get_bom_lines(self, bom, bom_quantity, product, line_id, level):
        components = []
        total = 0
        for line in bom.bom_line_ids:
            line_quantity = (bom_quantity / (bom.product_qty or 1.0)) * line.product_qty
            if line._skip_bom_line(product):
                continue
            company = bom.company_id or self.env.company
            price = line.product_id.uom_id._compute_price(line.product_id.with_context(force_company=company.id).standard_price, line.product_uom_id) * line_quantity
            if line.child_bom_id:
                factor = line.product_uom_id._compute_quantity(line_quantity, line.child_bom_id.product_uom_id) / line.child_bom_id.product_qty
                sub_total = self._get_price(line.child_bom_id, factor, line.product_id)
            else:
                sub_total = price
            sub_total = self.env.company.currency_id.round(sub_total)
            components.append({
                'po_no': line.x_studio_field_c9hp1,
                'part_no': line.customer_part_no,
                'description': line.x_studio_field_gVfQK,
                'manufacturer': line.manufacturer_id.name,
                'prod_id': line.product_id.id,
                'prod_name': line.product_id.display_name,
                'code': line.child_bom_id and line.child_bom_id.display_name or '',
                'prod_qty': line_quantity,
                'prod_uom': line.product_uom_id.name,
                'prod_cost': company.currency_id.round(price),
                'parent_id': bom.id,
                'line_id': line.id,
                'level': level or 0,
                'total': sub_total,
                'child_bom': line.child_bom_id.id,
                'phantom_bom': line.child_bom_id and line.child_bom_id.type == 'phantom' or False,
                'attachments': self.env['mrp.document'].search(['|', '&',
                    ('res_model', '=', 'product.product'), ('res_id', '=', line.product_id.id), '&', ('res_model', '=', 'product.template'), ('res_id', '=', line.product_id.product_tmpl_id.id)]),

            })
            total += sub_total
        return components, total
    
    
    def _get_pdf_line(self, bom_id, product_id=False, qty=1, child_bom_ids=[], unfolded=False):
        data = self._get_bom(bom_id=bom_id, product_id=product_id, line_qty=qty)

        def get_sub_lines(bom, product_id, line_qty, line_id, level):
            data = self._get_bom(bom_id=bom.id, product_id=product_id, line_qty=line_qty, line_id=line_id, level=level)
            bom_lines = data['components']
            lines = []
            for bom_line in bom_lines:
                lines.append({
                    'po_no': bom_line['po_no'],
                    'part_no': bom_line['part_no'],
                    'description': bom_line['description'],
                    'manufacturer': bom_line['manufacturer'],
                    'name': bom_line['prod_name'],
                    'type': 'bom',
                    'quantity': bom_line['prod_qty'],
                    'uom': bom_line['prod_uom'],
                    'prod_cost': bom_line['prod_cost'],
                    'bom_cost': bom_line['total'],
                    'level': bom_line['level'],
                    'code': bom_line['code'],
                    'child_bom': bom_line['child_bom'],
                    'prod_id': bom_line['prod_id']
                })
                if bom_line['child_bom'] and (unfolded or bom_line['child_bom'] in child_bom_ids):
                    line = self.env['mrp.bom.line'].browse(bom_line['line_id'])
                    lines += (get_sub_lines(line.child_bom_id, line.product_id.id, bom_line['prod_qty'], line, level + 1))
            if data['operations']:
                lines.append({
                    'name': _('Operations'),
                    'type': 'operation',
                    'quantity': data['operations_time'],
                    'uom': _('minutes'),
                    'bom_cost': data['operations_cost'],
                    'level': level,
                })
                for operation in data['operations']:
                    if unfolded or 'operation-' + str(bom.id) in child_bom_ids:
                        lines.append({
                            'name': operation['name'],
                            'type': 'operation',
                            'quantity': operation['duration_expected'],
                            'uom': _('minutes'),
                            'bom_cost': operation['total'],
                            'level': level + 1,
                        })
            return lines
        
        bom = self.env["mrp.bom"].browse(bom_id)
        product = product_id or bom.product_id or bom.product_tmpl_id.product_variant_id
        pdf_lines = get_sub_lines(bom, product, qty, False, 1)
        data["components"] = []
        data["lines"] = pdf_lines
        return data