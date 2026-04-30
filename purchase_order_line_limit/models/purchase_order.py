from odoo import api, fields, models, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        order = super(PurchaseOrder, self).create(vals)
        limit = order.company_id.purchase_order_line_limit
        if limit == 0 or len(order.order_line) <= limit:
            return order
        # Call the po split logic function
        self._split_purchase_order(order, limit)
        return order

    # Split the purchase order based on the company configuration
    def _split_purchase_order(self, order, limit):
        lines = order.order_line
        # Keep first original order
        main_lines = lines[:limit]
        extra_lines = lines[limit:]
        # Create new PO for remaining lines
        while extra_lines:
            current_extra_po_line = extra_lines[:limit]
            new_order = self.create({
                'partner_id': order.partner_id.id,
                'company_id': order.company_id.id,
                'currency_id': order.currency_id.id,
                'origin': order.origin,
            })
            for line in current_extra_po_line:
                line.write({'order_id': new_order.id})
            extra_lines -= current_extra_po_line