# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from urllib.parse import quote
import qrcode
import base64
import io


                        

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    _description = 'WorkOrder'


    image = fields.Binary("Image")
    url = fields.Text('URL')

    @api.model
    def create(self,vals):
        res = super(MrpWorkorder,self).create(vals)
        url = self.env['url.config'].search([('code', '=','WO')])
        if url.name:
            code = quote(res.product_id.x_studio_field_qr3ai,safe='')
            product = quote(res.product_id.default_code,safe='')
            qty = quote(str(res.qty_producing),safe='')
            routing = quote(res.name,safe='')
            production = quote(res.production_id.name,safe='')
            data= url.name + code + '/' + product + '/'+ qty + '/' + routing + '/' + production 
            img = qrcode.make(data)
            result = io.BytesIO()
            img.save(result, format='PNG')
            result.seek(0)
            img_bytes = result.read()
            base64_encoded_result_bytes = base64.b64encode(img_bytes)
            base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')
            res.image = base64_encoded_result_str
        return res