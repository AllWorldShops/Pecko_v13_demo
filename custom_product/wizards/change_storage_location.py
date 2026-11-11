from odoo import models, fields, api


class ChangeStorageLocationWizard(models.TransientModel):
    _name = 'change.storage.location.wizard'
    _description = 'Change Storage Location'

    storage_location = fields.Char(
        string='Storage Location',
        required=True
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        active_id = self.env.context.get('active_id')
        if active_id:
            product = self.env['product.template'].browse(active_id)
            res['storage_location'] = product.storage_location_id or ''

        return res

    def action_save(self):
        active_id = self.env.context.get('active_id')
        record = self.env['product.template'].sudo().browse(active_id)

        record.write({
            'storage_location_id': self.storage_location
        })

        return {'type': 'ir.actions.act_window_close'}