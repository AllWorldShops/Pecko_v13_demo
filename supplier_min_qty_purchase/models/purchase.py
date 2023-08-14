from odoo import api, fields, models, _



class PurchaseorderLine(models.Model):
    _inherit = 'purchase.order.line'


    def is_multiple(self, number, divisor):
        return number % divisor == 0

    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values, po):
        line_description = ''
        
        if values.get('product_description_variants'):
            line_description = values['product_description_variants']
        supplier = values.get('supplier')

        # customised by PPTS 
        # Purpose:- The quantity of purchase order should be based on minimum quantity in Vendor/Supplier under 'products'.
        ###############################################################################################
        if supplier.min_qty > 0:
            qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id)
            if qty > supplier.min_qty:
                sub_qty = (qty // supplier.min_qty) if self.is_multiple(qty, supplier.min_qty) else (qty // supplier.min_qty) + 1
                if qty == supplier.min_qty or supplier.min_qty <= 1:
                    pass
                else:
                    product_qty = supplier.min_qty * sub_qty
                    if product_uom != product_id.uom_po_id:
                        product_uom = product_id.uom_po_id

            if qty < supplier.min_qty:
                qty = product_uom._compute_quantity(supplier.min_qty, product_id.uom_po_id)
                product_qty = qty
                if product_uom != product_id.uom_po_id:
                    product_uom = product_id.uom_po_id
        ###############################################################################################

        res = self._prepare_purchase_order_line(product_id, product_qty, product_uom, company_id, supplier, po)
        # We need to keep the vendor name set in _prepare_purchase_order_line. To avoid redundancy
        # in the line name, we add the line_description only if different from the product name.
        # This way, we shoud not lose any valuable information.
        if line_description and product_id.name != line_description:
            res['name'] += '\n' + line_description
        res['date_planned'] = values.get('date_planned')
        res['move_dest_ids'] = [(4, x.id) for x in values.get('move_dest_ids', [])]
        res['orderpoint_id'] = values.get('orderpoint_id', False) and values.get('orderpoint_id').id
        res['propagate_cancel'] = values.get('propagate_cancel')
        res['product_description_variants'] = values.get('product_description_variants')
        return res