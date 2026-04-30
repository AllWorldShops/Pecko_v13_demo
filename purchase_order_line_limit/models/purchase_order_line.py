from odoo import api, fields, models, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def create(self, vals):
        line = super(PurchaseOrderLine, self).create(vals)
        order = line.order_id
        limit = order.company_id.purchase_order_line_limit

        if limit == 0 or len(order.order_line) <= limit:
            return line

        # Call the po split logic function
        self._split_purchase_order(order, limit)
        return line


    # Split the purchase order based on the company configuration
    def _split_purchase_order(self, order, limit):
        lines = order.order_line

        # Keep first original order
        main_lines = lines[:limit]
        extra_lines = lines[limit:]

        # Create new PO for remaining lines
        while extra_lines:
            current_extra_po_line = extra_lines[:limit]

            new_order = order.create({
                'partner_id': order.partner_id.id,
                'company_id': order.company_id.id,
                'currency_id': order.currency_id.id,
            })

            for line in current_extra_po_line:
                line.write({'order_id': new_order.id})

            extra_lines -= current_extra_po_line