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
            if res.product_id.x_studio_field_qr3ai:
                code = quote(res.product_id.x_studio_field_qr3ai,safe='')
            else:
                code = ''
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

    def qrcode_image(self):
        wo_id = self.env['mrp.workorder'].search([('state','in',('pending','ready'))],limit=4000)
        if wo_id:
            url = self.env['url.config'].search([('code', '=','WO')])
            for rec in wo_id:
                if url.name and not rec.image:
                    if rec.product_id.x_studio_field_qr3ai:
                        code = quote(rec.product_id.x_studio_field_qr3ai,safe='')
                    else:
                        code = ''
                    product = quote(rec.product_id.default_code,safe='')
                    qty = quote(str(rec.qty_producing),safe='')
                    routing = quote(rec.name,safe='')
                    production = quote(rec.production_id.name,safe='')
                    data= url.name + code + '/' + product + '/'+ qty + '/' + routing + '/' + production 
                    img = qrcode.make(data)
                    result = io.BytesIO()
                    img.save(result, format='PNG')
                    result.seek(0)
                    img_bytes = result.read()
                    base64_encoded_result_bytes = base64.b64encode(img_bytes)
                    base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')
                    rec.image = base64_encoded_result_str