from odoo import models, fields, api , _
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    excess_quantity_allow = fields.Boolean(string="Excess Quantity Allow" , config_parameter='delivery_quantity.excess_quantity_allow')


class StockQuantity(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        str_product = self.env['ir.config_parameter'].sudo().get_param('delivery_quantity.excess_quantity_allow')
        print(str_product,"str_product")
        if str_product:
            for line in self.move_ids_without_package.filtered(
                        lambda l: l.quantity_done > l.product_uom_qty and self.picking_type_code == 'outgoing' and l.sale_line_id):

                    raise ValidationError(
                        _("Product level does not allow for more quantity to be delivered - '%s'") % (
                            line.product_id.name))
        return super().button_validate()