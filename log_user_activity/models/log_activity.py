from odoo import fields, models, api
from datetime import datetime

class LogActivity(models.Model):
    _name = "log.activity"

    name = fields.Char('Name')
    model_id = fields.Many2one('ir.model', string="Model")
    user_id = fields.Many2one('res.users', string="Updated By")
    updated_at = fields.Datetime("Updated at")
    field_name = fields.Char('Field Name')
    previous_value = fields.Float('Previous Value')
    current_value = fields.Float('Current Value')
    record_id = fields.Char('Record ID')
    record_ref = fields.Char('Reference')

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def write(self, values):
        model_id = self.env['ir.model']._get(str(self._name))
        if 'reserved_uom_qty' in values:
            # Find the existing log record
            log_record = self.env['log.activity'].search([('model_id', '=', model_id.id), ('record_id', '=', self.id), ('field_name', '=', 'reserved_qty')], limit=1)

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
                'updated_at': datetime.now(),
                'field_name': 'reserved_uom_qty',
                'previous_value': self.reserved_uom_qty,
                'current_value': values['reserved_uom_qty'],
                'record_id': str(self.id),
                'record_ref': self.reference
            })

        return super(StockMoveLine, self).write(values)

    # def write(self, vals):

    #     log_activity = self.env['log.activity']
    #     field_vals = {}
    #     if 'reserved_uom_qty' in vals:
    #         field_vals.update({'reserved_uom_qty': vals['reserved_uom_qty']})
    #     if 'reserved_qty' in vals:
    #         field_vals.update({'reserved_qty': vals['reserved_qty']})

    #     model_id = self.env['ir.model']._get(str(self._name))
    #     res = super(StockMoveLine, self).write(vals)
    #     existing_log = log_activity.search([('record_id', '=', self.id), ('model_id', '=',str(self._name))])
    #     for log in existing_log:
    #         if log.field_name == 'reserved_uom_qty' and field_vals['reserved_uom_qty']:
    #             log.previous_value = log.current_value
    #             log.current_value = field_vals['reserved_uom_qty']

    #         if log.field_name == 'reserved_qty' and field_vals['reserved_qty']:
    #             log.previous_value = log.current_value
    #             log.current_value = field_vals['reserved_qty']

    #     if not existing_log and self:
    #         print("sssss")
    #         # for key, vals in field_vals.items():
    #         log_activity.create({
    #             'model_id': model_id.id,
    #             'user_id': self.env.user.id,
    #             'updated_at': datetime.now(),
    #             'field_name': key,
    #             # 'previous_value': vals,
    #             # 'current_value': vals,
    #             'record_id': self.id,
    #             'record_ref': self.reference
    #         })

    #     return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    def write(self, values):
        model_id = self.env['ir.model']._get(str(self._name))

        if "forecast_availability" in values:
            # Find the existing log record
            log_record = self.env['log.activity'].search([('model_id', '=', model_id.id), ('record_id', '=', self.id), ('field_name', '=', 'reserved_availability')], limit=1)

            # Update the existing log record or create a new one if not found
            # if log_record:
            #     log_record.write({
            #         'previous_value': self.reserved_availability,
            #         'current_value': values['reserved_availability'],
            #         'updated_at': datetime.now(),
            #     })

            # else:
            self.env['log.activity'].create({
                'model_id': model_id.id,
                'user_id': self.env.user.id,
                'updated_at': datetime.now(),
                'field_name': 'forecast_availability',
                'previous_value': self.forecast_availability,
                'current_value': values['forecast_availability'],
                'record_id': str(self.id),
                'record_ref': self.reference
            })

        return super(StockMove, self).write(values)
    

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def write(self, values):
        model_id = self.env['ir.model']._get(str(self._name))
        if 'reserved_quantity' in values:
            # Find the existing log record
            log_record = self.env['log.activity'].search([('model_id', '=', model_id.id), ('record_id', '=', self.id), ('field_name', '=', 'reserved_quantity')], limit=1)
            # Update the existing log record or create a new one if not found
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
                'updated_at': datetime.now(),
                'field_name': 'reserved_quantity',
                'previous_value': self.reserved_quantity,
                'current_value': values['reserved_quantity'],
                'record_id': str(self.id),
                'record_ref': self.product_id.display_name
            })

        return super(StockQuant, self).write(values)
        



    