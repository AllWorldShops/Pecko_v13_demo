from odoo import api, fields, models,_
from odoo.exceptions import ValidationError

class FinancialYear(models.Model):
    _name = 'financial.year'
    _description = 'Financial Year'

    name = fields.Char(string='Financial Year')

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if rec.name and self.search([('name','=', rec.name),('id','!=', rec.id)]):
                raise ValidationError(_('Financial Year already exists'))
