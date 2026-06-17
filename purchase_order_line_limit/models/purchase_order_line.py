from odoo import api, models

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def create(self, vals):
        line = super().create(vals)

        order = line.order_id
        product_id = line.product_id.id
        partner_id = order.partner_id.id
        user_id = order.user_id.id
        limit = order.company_id.purchase_order_line_limit

        # Check duplicate in current PO
        existing_line = self.search([
            ('order_id', '=', order.id),
            ('product_id', '=', product_id),
            ('id', '!=', line.id),
        ], limit=1)

        if existing_line:
            existing_line.product_qty += line.product_qty
            line.unlink()
            return existing_line

        # Check duplicate in other draft POs
        child_orders = self.env['purchase.order'].search([
            ('state', '=', 'draft'),
            ('partner_id', '=', partner_id),
            ('user_id', '=', user_id),
            ('id', '!=', order.id),
        ])

        existing_child_line = self.search([
            ('order_id', 'in', child_orders.ids),
            ('product_id', '=', product_id),
        ], limit=1)

        if existing_child_line:
            existing_child_line.product_qty += line.product_qty
            line.unlink()
            return existing_child_line

        # Split only when limit exceeded
        if limit and len(order.order_line) > limit:
            self._split_purchase_order(order)

        return line

    def _split_purchase_order(self, order):
        PurchaseOrder = self.env['purchase.order']

        limit = order.company_id.purchase_order_line_limit
        if not limit:
            return

        extra_lines = order.order_line[limit:]
        partner_id = order.partner_id.id

        while extra_lines:

            current_lines = extra_lines[:limit]

            # Reuse existing draft PO if space available
            existing_po = PurchaseOrder.search([
                ('partner_id', '=', partner_id),
                ('state', '=', 'draft'),
                ('id', '!=', order.id),
            ], order='id desc', limit=1)

            if not existing_po or len(existing_po.order_line) >= limit:
                existing_po = PurchaseOrder.create({
                    'partner_id': order.partner_id.id,
                    'company_id': order.company_id.id,
                    'currency_id': order.currency_id.id,
                    'user_id': order.user_id.id,
                })

            for line in current_lines:

                duplicate_line = self.search([
                    ('order_id', '=', existing_po.id),
                    ('product_id', '=', line.product_id.id),
                ], limit=1)

                if duplicate_line:
                    duplicate_line.product_qty += line.product_qty
                    line.unlink()
                else:
                    line.order_id = existing_po.id

            extra_lines -= current_lines