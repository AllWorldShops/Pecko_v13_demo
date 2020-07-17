# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer/Customer Name')
    storage_location_id = fields.Char(string='Storage Location')

    
class ProductProduct(models.Model):
    _inherit = 'product.product'
 
    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer/Customer Name',related='product_tmpl_id.manufacturer_id',store=True)
    storage_location_id = fields.Char(string='Storage Location',related='product_tmpl_id.storage_location_id')
   
#     @api.multi
    def write(self, vals):
        rec = super(ProductProduct, self).write(vals)
        if vals.get('manufacturer_id'):
            product_id = self.env['product.product'].search([('id','=',self.id)])
            product_id.product_tmpl_id.manufacturer_id = vals.get('manufacturer_id')
        return rec