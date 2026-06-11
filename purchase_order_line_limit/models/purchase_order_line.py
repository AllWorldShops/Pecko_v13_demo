from odoo import api, fields, models, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def create(self, vals):
        line = super(PurchaseOrderLine, self).create(vals)
        order = line.order_id
        product_id = line.product_id.id
        partner_id = line.order_id.partner_id.id if line.order_id.partner_id else False
        user_id = line.order_id.user_id.id if line.order_id.user_id else False
        order_lines = order.order_line
        limit = order.company_id.purchase_order_line_limit

        existing_line = order.order_line.filtered(
            lambda l: l.id != line.id and l.product_id.id == product_id
        )

        # child_order = self.env['purchase.order'].search([('parent_purchase_order_id', 'in', [order.id, parent_purchase_order_id]), ('state', '=', 'draft'), ('user_id', '=', user_id), ('partner_id', '=', partner_id),], order='id')
        child_order = self.env['purchase.order'].search([('state', '=', 'draft'), ('user_id', '=', user_id), ('partner_id', '=', partner_id),], order='id')
        existing_child_order_lines = child_order.order_line.filtered(
            lambda l: l.id != line.id and l.product_id.id == product_id
        )

        if existing_line:
            existing_line[0].product_qty += line.product_qty
            # Remove duplicate line
            line.sudo().unlink()
            # Return existing line
            return existing_line[0]

        if existing_child_order_lines:
            existing_child_order_lines[0].product_qty += line.product_qty
            existing_order = existing_child_order_lines[0].order_id
            # Remove duplicate line
            line.sudo().unlink()
            # Return existing line
            return existing_child_order_lines[0]

        if limit == 0 or len(order_lines) <= limit:
            return line

        # Call the po split logic function
        self._split_purchase_order(order, limit)
        return line

    # Split the purchase order based on the company configuration
    def _split_purchase_order(self, order, limit):
        lines = order.order_line
        partner_id = order.partner_id.id if order.partner_id else False
        PurchaseOrder = self.env['purchase.order']
        limit = order.company_id.purchase_order_line_limit

        # Keep first original order
        extra_lines = lines[limit:]
        # Create new PO for remaining lines
        while extra_lines:
            current_extra_po_line = extra_lines[:limit]

            existing_po = False

            for po in self.env['purchase.order'].search([
                ('partner_id', '=', partner_id),  ('state', '=', 'draft'),
            ], order='id desc'):
                if len(po.order_line) < limit:
                    existing_po = po
                    break

            if not existing_po:
                new_order = PurchaseOrder.create({
                    'partner_id': order.partner_id.id,
                    'company_id': order.company_id.id,
                    'currency_id': order.currency_id.id,
                    'user_id': order.user_id.id if order.user_id else False,
                })
            else:
                new_order = existing_po

            for line in current_extra_po_line:

                existing_line = self.env['purchase.order.line'].search([
                    ('order_id', '=', new_order.id),
                    ('partner_id', '=', partner_id),
                    ('product_id', '=', line.product_id.id),
                ], limit=1)

                if existing_line:
                    existing_line.product_qty += line.product_qty
                    # Remove duplicate line
                    line.sudo().unlink()
                else:
                    line.write({
                        'order_id': new_order.id
                    })

            extra_lines -= current_extra_po_line