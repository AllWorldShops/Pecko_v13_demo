from odoo import fields, models, api, _


class DriverMaster(models.Model):
    _name = 'driver.master'

    name = fields.Char("Driver Name", required=True)
    ph_no = fields.Char("Phone Number")