from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError


class AcmoveInherit(models.Model):
    _inherit = 'account.move'
    
    receipts_id = fields.Many2one('stock.picking', string="Receipts",
     states={'draft': [('readonly', False)]})
    picking_ids = fields.Many2many('stock.picking', string="Picking_ids")


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(AcmoveInherit, self)._onchange_partner_id()
        for rec in self:
            return {'domain': {'receipts_id':[('partner_id', '=', rec.partner_id.id),('state', '=', 'done'),
                                              ('picking_type_id.code', '=', 'incoming')]}}
        return res


    @api.onchange('receipts_id')
    def onchange_receipts_id(self):
        company = self.company_id
        currency = self.currency_id
        company_currency = company.currency_id
        date = self.date or fields.Date.context_today(self)
        id_list = []
        if self.receipts_id:
            receipt_lines = []
            for line in self.receipts_id.move_ids_without_package:
                product_price_unit = line.purchase_line_id.price_unit
                if currency and currency != company_currency:
                    product_price_unit = company_currency._convert(line.purchase_line_id.price_unit, currency,
                                                                   company, date)

                self.invoice_line_ids += self.env['account.move.line'].new({
                    'position_no':line.position_no,
                    'product_id':line.product_id.id,
                    'customer_part_no': line.product_id.name,
                    'manufacturer_id': line.manufacturer_id.id,
                    'name' : line.product_id.default_code,
                    # 'quantity':line.purchase_line_id.qty_received if line.purchase_line_id else line.quantity_done,
                    'quantity': line.quantity / line.purchase_line_id.product_uom.factor_inv if line.purchase_line_id and line.product_uom.id != line.purchase_line_id.product_uom.id else line.quantity,
                    'price_unit': line.purchase_line_id.price_unit if line.purchase_line_id else line.product_id.standard_price,
                    'account_id': line.product_id.categ_id.property_stock_account_input_categ_id.id or False,
                    'name':line.product_id.name,
                    'tax_ids': line.purchase_line_id.taxes_id.ids if line.purchase_line_id else False,
                    'product_uom_id': line.purchase_line_id.product_uom.id if line.purchase_line_id else line.product_uom.id,
                    # 'st_move_id': line.id,
                }
            )
            id_list.append(self.receipts_id.id)

            for rec in self:
                if rec.receipts_id.id in rec.picking_ids.ids:
                    pass
                else:
                    rec.picking_ids = [(4, x, None) for x in id_list]

                for i_line in rec.invoice_line_ids:
                    i_line.name = i_line.product_id.default_code or ''
                
