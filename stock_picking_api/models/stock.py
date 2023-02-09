from odoo import fields, models, api, _
import requests
import json
import logging
_logger = logging.getLogger(__name__)



class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    driver_id = fields.Many2one('driver.master', string="Assign To")
    pod_status = fields.Char("POD Status")
    pod_date = fields.Datetime("POD Date/Time")
    pod_image = fields.Binary(string="POD")

    def action_done(self):
        res = super(StockPickingInherit, self).action_done()
        # for picking_id in self:
            # print(picking_id.state, "picking_id.state")
        if self.state == 'done' and self.picking_type_id.code == 'outgoing' and self.sale_id and self.company_id.country_id.code in ['SG', 'MY']:
            url = self.env['url.config'].search([('code', '=', 'DO'),('active', '=', True)], limit=1)
            if url:
                headers = {'Content-Type': 'application/json', 'X-API-KEY': '2fe3ddf50048acc2231e184f230750ab59dcb9474bbaba6b'}
                street1 = (self.partner_id.street + ", " if self.partner_id.street else "")
                street2 = (self.partner_id.street2  if self.partner_id.street2 else "")
                city = (self.partner_id.city +  ", " if self.partner_id.city else "")
                state = (self.partner_id.state_id.name + ", " if self.partner_id.state_id else "")
                country = (self.partner_id.country_id.name  if self.partner_id.country_id else "")
                delivery_address = self.partner_id.name + ", \n" + street1 + street2 + "\n" + city + state + country
                driver = str(self.driver_id.name) if self.driver_id else ""
                move_items = []
                for line in self.move_line_ids_without_package:
                    move_items.append({
                        'sku' : line.product_id.default_code,
                        'description': str(line.part_no),
                        'quantity': str(line.qty_done),
                    })
                data = {
                    "data": {
                        "type": "Delivery",
                        "do_number": self.name,
                        "date": str(self.date_done.date()),
                        "address": delivery_address,
                        'assign_to': driver,
                        "items": move_items
                        }
                    }
                data_json = json.dumps(data)
                url = str(url.name)
                try:
                    r = requests.post(url=url, headers=headers, data=data_json)
                except Exception as e:
                    _logger.info("---------Exception Occured ---------: %s", str(e))
                
        return res