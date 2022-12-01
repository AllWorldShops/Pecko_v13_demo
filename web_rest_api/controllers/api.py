import json
import pytz

from odoo import http, fields, _
from odoo.http import request
from datetime import datetime
from dateutil import parser
import logging
_logger = logging.getLogger(__name__)
import base64
import requests

req_env = request.httprequest.headers.environ

class RestApi(http.Controller):


    def get_as_base64(self, url):
        res = base64.b64encode(requests.get(url).content)
        _logger.info('------Image ------: %s' % str(res))
        return res

    @http.route([
        '/api/<string:model>/<string:method>',
        '/api/<string:model>/<string:method>/<string:id>'
        ], type='json', auth="none", csrf=False)
    def odoo_rest_api(self, model=None, method=None, id=None, **kw):
        token = kw.get('token', False)
        domain = kw.get('domain', [])
        offset = kw.get('offset', 0)
        limit = kw.get('limit', 0)
        fields = kw.get('fields', [])
        vals = kw.get('vals', {})
        args = kw.get('args', [])
        is_guest = kw.get('is_guest', False)
        result = {}
        data = {}
        user_id = False
        headers = dict(request.httprequest.headers.items())
        print(kw)

        _logger.info('Website Lead - API Data: %s' % vals)
        
        # Webhook part starts

        if model and method:
            webhook_vals = {}
            helpdesk_tickets = {}
            _logger.info('model----------: %s' % model)
            _logger.info('method----------: %s' % method)
            
            # http://kuesv13.pptssolutions.com/api/whatsapp.webhook/create?vals=
            # webhook_data = json.loads(request.httprequest.args)
            webhook_data = json.loads(request.httprequest.data)
            _logger.info('------WEBHOOK DATA ------: %s' % str(webhook_data))
            if model == 'detrack.do' and method == 'create' and webhook_data:
                _logger.info('detrack.do----------')

                # Authorization starts
                picking_id = request.env['stock.picking'].sudo().search([('name', '=', webhook_data['do_number'])], limit=1)
                if picking_id:
                    created_at = parser.parse(webhook_data['created_at']) 
                    pod_date = created_at.replace(tzinfo=None)

                    if webhook_data['photo_1_file_url'] != None:
                        url = webhook_data['photo_1_file_url']
                        img = self.get_as_base64(url)
                        # _logger.info('------Image ------: %s' % str(img))
                        # _logger.info('------tracking_status ------ :%s' % str(webhook_data['tracking_status']))
                        record = picking_id.sudo().write({'pod_status': webhook_data['tracking_status'],
                                                        'pod_date': pod_date,
                                                        'pod_image': img})
                        _logger.info('Detrack Webhook Record Updated with image------ %s' % picking_id.pod_status)
                    else:
                        record = picking_id.sudo().write({'pod_status': webhook_data['tracking_status'],
                                                        'pod_date': pod_date})
                        _logger.info('Detrack Webhook Record Updated without image------ %s' % picking_id.pod_status)

                # stop


                # result.update({'status': True, 'id':record.id, 'message':"Created successfully"})

        # Webhook part ends
