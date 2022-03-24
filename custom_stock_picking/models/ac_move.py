from odoo import models, fields, api, _
from datetime import date

class AcmoveInherit(models.Model):
    _inherit = 'account.move'
    
    receipts_id = fields.Many2one('stock.picking', string="Receipts", store=False, domain=[('state', '=', 'done'),('picking_type_id.code', '=', 'incoming')])
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(AcmoveInherit, self)._onchange_partner_id()
        for rec in self:
            # if rec.partner_id:
            return {'domain': {'receipts_id':[('partner_id', '=', rec.partner_id.id),('state', '=', 'done'),('picking_type_id.code', '=', 'incoming')]}}
        return res
    
    @api.onchange('receipts_id')
    def onchange_receipts_id(self):
        company = self.company_id
        currency = self.currency_id
        company_currency = company.currency_id
        date = self.date or fields.Date.context_today(self)
        if self.receipts_id:
            receipt_lines = []
            for rec in self:
                account_id = self.env['account.account'].sudo().search([('deprecated', '=', False),('user_type_id.type', 'not in', ['receivable', 'payable']),('company_id','=',self.company_id.id)],limit=1)
                for line in self.receipts_id.move_ids_without_package:
                    product_price_unit = line.purchase_line_id.price_unit
                    if currency and currency != company_currency:
                        product_price_unit = company_currency._convert(line.purchase_line_id.price_unit, currency, company, date)
                    print(product_price_unit, "product_price_unittt")
                    val = {
                    'product_id':line.product_id.id,
                    'quantity':line.quantity_done,
                    'price_unit': product_price_unit,
                    'account_id': account_id.id if account_id else False,
                    'name':line.product_id.name,
                    'tax_ids': line.purchase_line_id.taxes_id.ids,
                    'product_uom_id': line.product_uom.id if line.product_uom else line.product_id.uom_id.id,
                    # 'price_subtotal': line.quantity_done * product_price_unit,
                    }
                    receipt_lines.append((0, 0, val))
                    if not rec.invoice_line_ids:
                        rec.invoice_line_ids = receipt_lines
                        self._onchange_currency()
                    else:
                        for i_line in rec.invoice_line_ids:
                            i_line.update(val)
                            i_line.move_id._onchange_currency()


        
            
        

    

        
        
    
    
    