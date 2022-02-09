# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict
from odoo import models, fields, api

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
    
#     @api.multi
    def write(self, vals):
        rec = super(ProductProduct, self).write(vals)
        if vals.get('manufacturer_id'):
            product_id = self.env['product.product'].search([('id','=',self.id)])
            product_id.product_tmpl_id.manufacturer_id = vals.get('manufacturer_id')
        return rec
    
class ResCompanyInh(models.Model):
    _inherit = 'res.company'
    
    logo_one = fields.Binary("DO Report Logo")
    logo_two = fields.Binary("PO Report Logo")
    logo_three = fields.Binary("Invoice Report Logo")

            