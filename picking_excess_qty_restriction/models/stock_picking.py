from odoo import models, fields, api , _
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    excess_quantity_allow = fields.Boolean(string="Excess Quantity Allow" , config_parameter='delivery_quantity.excess_quantity_allow')


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    def button_validate(self):
        delivery_qty = self.env['ir.config_parameter'].sudo().get_param('delivery_quantity.excess_quantity_allow')
        if delivery_qty:
            for line in (self.move_ids_without_package.filtered
                (lambda l: round(l.quantity,4) > l.product_uom_qty and self.picking_type_id.code in ['outgoing','incoming','internal','mrp_operation'])):
                    raise ValidationError(
                        _("Product level does not allow for more quantity to be delivered - '%s' Demand - '%s' Done - '%s'")
                        % (line.product_id.name,line.product_uom_qty,line.quantity))
        return super(StockPicking,self).button_validate()