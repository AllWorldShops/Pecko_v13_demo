from odoo import fields, models, api
from datetime import datetime

class LogActivity(models.Model):
    _name = "log.activity"
    _order = 'updated_at desc'

    name = fields.Char('Name')
    model_id = fields.Many2one('ir.model', string="Model")
    user_id = fields.Many2one('res.users', string="Updated By")
    product_id = fields.Many2one('product.product', string="Product")
    company_id = fields.Many2one('res.company', string="Company")
    updated_at = fields.Datetime("Updated at")
    field_name = fields.Char('Field Name')
    previous_value = fields.Float('Previous Value')
    current_value = fields.Float('Current Value')
    record_id = fields.Char('Record ID')
    record_ref = fields.Char('Reference')

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.model_create_multi
    def create(self, vals):
        model_id = self.env['ir.model']._get(str(self._name))
        # print(vals['reserved_uom_qty'] > 0, "vals['reserved_uom_qty'] > 0++++++++++++++")
        logs = []
        for value in vals:
            if 'reserved_uom_qty' in value:
                log = self.env['log.activity'].create({
                        'model_id': model_id.id,
                        'user_id': self.env.user.id,
                        'company_id': self.env.company.id,
                        'updated_at': datetime.now(),
                        'field_name': 'reserved_uom_qty',
                        'previous_value': self.reserved_uom_qty,
                        'current_value': value['reserved_uom_qty'],
                        # 'record_id': str(self.id),
                        # 'record_ref': self.reference
                    })
                logs.append(log)

        res = super(StockMoveLine, self).create(vals)
        for rec in res:
            for log in logs:
                log.write({
                    'record_id': str(rec.id),
                    'record_ref': rec.reference,
                    'product_id': rec.product_id.id,
                })
        return res

    def write(self, values):
        model_id = self.env['ir.model']._get(str(self._name))
        if 'reserved_uom_qty' in values and values['reserved_uom_qty']:
            # Find the existing log record
            # log_record = self.env['log.activity'].search([('model_id', '=', model_id.id), ('record_id', '=', self.id), ('field_name', '=', 'reserved_qty')], limit=1)

            # Update the existing log record or create a new one if not found
            # if log_record:
            #     log_record.write({
            #         'previous_value': self.reserved_qty,
            #         'current_value': values['reserved_qty'],
            #         'updated_at': datetime.now(),
            #     })
            # else:
            self.env['log.activity'].create({
                'model_id': model_id.id,
                'user_id': self.env.user.id,
                'company_id': self.env.company.id,
                'updated_at': datetime.now(),
                'field_name': 'reserved_uom_qty',
                'previous_value': self.reserved_uom_qty,
                'current_value': values['reserved_uom_qty'],
                'record_id': str(self.id),
                'record_ref': self.reference,
                'product_id': self.product_id.id,
            })

        return super(StockMoveLine, self).write(values)


# class StockMove(models.Model):
#     _inherit = 'stock.move'

#     @api.model_create_multi
#     def create(self, vals):
#         model_id = self.env['ir.model']._get(str(self._name))
#         log = False
#         if vals and 'forecast_availability' in vals[0]:
#             log = self.env['log.activity'].create({
#                     'model_id': model_id.id,
#                     'user_id': self.env.user.id,
#                     'company_id': self.env.company.id,
#                     'updated_at': datetime.now(),
#                     'field_name': 'forecast_availability',
#                     'previous_value': self.forecast_availability,
#                     'current_value': vals[0]['forecast_availability'],
#                     # 'record_id': str(self.id),
#                     # 'record_ref': self.reference
#                 })
#         return super(StockMove, self).create(vals)

#     def write(self, values):
#         model_id = self.env['ir.model']._get(str(self._name))
#         if "forecast_availability" in values:
#             self.env['log.activity'].create({
#                 'model_id': model_id.id,
#                 'user_id': self.env.user.id,
#                 'company_id': self.env.company.id,
#                 'updated_at': datetime.now(),
#                 'field_name': 'forecast_availability',
#                 'previous_value': self.forecast_availability,
#                 'current_value': values['forecast_availability'],
#                 'record_id': str(self.id),
#                 'record_ref': self.reference
#             })

#         return super(StockMove, self).write(values)
    

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def write(self, values):
        model_id = self.env['ir.model']._get(str(self._name))
        if 'reserved_quantity' in values:
            # Find the existing log record
            # log_record = self.env['log.activity'].search([('model_id', '=', model_id.id), ('record_id', '=', self.id), ('field_name', '=', 'reserved_quantity')], limit=1)
            # # Update the existing log record or create a new one if not found
            # if log_record:
            #     log_record.write({
            #         'previous_value': self.reserved_quantity,
            #         'current_value': values['reserved_quantity'],
            #         'updated_at': datetime.now(),
            #     })
            # else:
            self.env['log.activity'].create({
                'model_id': model_id.id,
                'user_id': self.env.user.id,
                'company_id': self.env.company.id,
                'updated_at': datetime.now(),
                'field_name': 'reserved_quantity',
                'previous_value': self.reserved_quantity,
                'current_value': values['reserved_quantity'],
                'record_id': str(self.id),
                'record_ref': self.product_id.display_name,
                'product_id': self.product_id.id,
            })

        return super(StockQuant, self).write(values)
        



    