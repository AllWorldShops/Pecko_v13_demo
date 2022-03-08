from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    workorder_flag = fields.Boolean("Workorder Functionality",config_parameter='custom_mrp.workorder_flag')

