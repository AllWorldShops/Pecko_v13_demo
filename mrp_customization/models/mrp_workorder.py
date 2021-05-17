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
    critical_task = fields.Boolean("Critical Task",readonly=True, related='operation_id.critical_task', store=True)


    @api.model
    def create(self,vals):
        res = super(MrpWorkorder,self).create(vals)
        url = self.env['url.config'].search([('code', '=','WO')])
        if url.name:
            if res.product_id.x_studio_field_qr3ai:
                code = quote(res.product_id.x_studio_field_qr3ai,safe='')
            else:
                code = ''
            if res.critical_task:
                critical_task = "1"
            else:
                critical_task = "0"
            if not res.production_id.date_start_wo:
                raise UserError(_('Kindly enter the WorkOrder Start date'))
            date_start = res.production_id.date_start_wo.strftime("%Y-%m-%d")
            task_code = quote(critical_task,safe='')
            company = quote("PM",safe='')
            date_code = quote(date_start,safe='')
            product = quote(res.product_id.default_code,safe='')   
            qty = quote(str(res.qty_producing),safe='')
            routing_single_encode = quote(res.name,safe='')
            routing = quote(routing_single_encode,safe='')
            production = quote(res.production_id.name,safe='')
            production_double_code = quote(production,safe='')
            data= url.name + code + '/' + product + '/'+ qty + '/' + routing + '/' + production_double_code + "/" + date_code + "/" + task_code + "/" + company 
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
        wo_id = self.env['mrp.workorder'].search([('state','in',('pending','ready')),('image','=',False)],limit=2000)
        if wo_id:
            url = self.env['url.config'].search([('code', '=','WO')])
            for rec in wo_id:
                if url.name and not rec.image:
                    if rec.product_id.x_studio_field_qr3ai:
                        code = quote(rec.product_id.x_studio_field_qr3ai,safe='')
                    else:
                        code = ''
                    if rec.critical_task:
                        critical_task = "1"
                    else:
                        critical_task = "0"
                    # if not rec.production_id.date_start_wo:
                    #     raise UserError(_('Kindly enter the WorkOrder Start date'))
                    if rec.production_id.date_start_wo:
                        date_start = rec.production_id.date_start_wo.strftime("%Y-%m-%d")
                    else:
                        date_start = ''
                    task_code = quote(critical_task,safe='')
                    company = quote("PM",safe='')
                    date_code = quote(date_start,safe='')
                    product = quote(rec.product_id.default_code,safe='')
                    qty = quote(str(rec.qty_producing),safe='')
                    routing_single_encode = quote(rec.name,safe='')
                    routing = quote(routing_single_encode,safe='')
                    production = quote(rec.production_id.name,safe='')
                    production_double_code = quote(production,safe='')
                    data= url.name + code + '/' + product + '/'+ qty + '/' + routing + '/' + production_double_code + "/" + date_code + "/" + task_code + "/" + company
                    img = qrcode.make(data)
                    result = io.BytesIO()
                    img.save(result, format='PNG')
                    result.seek(0)
                    img_bytes = result.read()
                    base64_encoded_result_bytes = base64.b64encode(img_bytes)
                    base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')
                    rec.image = base64_encoded_result_str

    def image_url_redirect(self):
        url = self.env['url.config'].search([('code', '=','WO')])
        if url.name and self.image:
            if self.product_id.x_studio_field_qr3ai:
                code = quote(self.product_id.x_studio_field_qr3ai,safe='')
            else:
                code = ''
            if self.critical_task:
                critical_task = "1"
            else:
                critical_task = "0"
            if not self.production_id.date_start_wo:
                raise UserError(_('Kindly enter the WorkOrder Start date'))
            date_start = self.production_id.date_start_wo.strftime("%Y-%m-%d")
            task_code = quote(critical_task,safe='')
            company = quote("PM",safe='')
            date_code = quote(date_start,safe='')
            product = quote(self.product_id.default_code,safe='')
            qty = quote(str(self.qty_producing),safe='')
            routing_single_encode = quote(self.name,safe='')
            routing = quote(routing_single_encode,safe='')
            production = quote(self.production_id.name,safe='')
            production_double_code = quote(production,safe='')
            data = url.name + code + '/' + product + '/'+ qty + '/' + routing + '/' + production_double_code + "/" + date_code + "/" + task_code + "/" + company
            return {   
                  'name'     : 'Go to website',
                  'res_model': 'ir.actions.act_url',
                  'type'     : 'ir.actions.act_url',
                  'url'      :  data
               }

class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'
    _description = 'Work Center Usage'


    critical_task = fields.Boolean("Critical task")               