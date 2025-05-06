from odoo import fields, models, api, _
from odoo.http import request


class BucketDays(models.TransientModel):
    _name = 'bucket.days'
    days=fields.Integer(string="Bucket Days",default=30)
    
    # @api.multi
    def report_aged_receivable(self):
#         request.session['days'] = self.days
#         print (request.session['days'])
        context = {
            'model': 'account.aged.receivable',
            'days': self.days,
            'context': {'days': self.days,}
            }
        return {
            'type': 'ir.actions.client',
            'name': 'Aged Receivable',
            'tag': 'account_report',
            'context': context
            }