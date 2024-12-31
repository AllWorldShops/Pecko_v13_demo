import base64
import csv
from io import StringIO
from docutils.nodes import reference
from odoo import models, fields, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from datetime import date
import logging
_logger = logging.getLogger(__name__)

# Manually update the valuation and stock journal using xl sheet
class ImportStockValuation(models.TransientModel):
    _name = "import.stock.valuation"

    file = fields.Binary(string='File')

    def import_stock_valuation_data(self):
        csv_data = base64.b64decode(self.file)
        csv_string = csv_data.decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_string))
        reference_count = 1
        for row in csv_reader:
            if row:
                create_date = row['Date']
                date_val= date.today()
                # stock_move = self.env['stock.move'].search([('reference', '=', row['Reference'])],limit=1)
                product = self.env['product.product'].search(
                [ '|', ('active', '=', True), ('active', '=', False), ('default_code', '=', row['Product'])], limit=1)
                _logger.info("%s product", product.name)

                if not product:
                    raise UserError(_("Product not found: %s") % row['Product'])

                on_hand_check= product.with_context({'to_date': date_val}).qty_available
                _logger.debug("%s on_hand_check", on_hand_check)
                if on_hand_check > 0.0:
                    _logger.info("%s =======", on_hand_check)
                    continue
                if product:
                    product_id = product
                quantity = row['Done']
                company_id = self.env['res.company'].search([('name', '=', row['Company'])])
                unit_cost = row['Unit Cost']
                # unit_cost = product_id.standard_price
                value = float(unit_cost) * float(quantity)

                stock_valuation = self.env['stock.valuation.layer'].create({
                    'create_date': create_date,
                    # 'stock_move_id': stock_move.id or False,
                    'product_id': product_id.id or False,
                    'company_id': company_id.id or False,
                    'quantity': quantity,
                    'unit_cost': unit_cost,
                    'value': value,

                })
                _logger.info("%s stock_valuation", stock_valuation)

                self.env.cr.execute(
                    'UPDATE stock_valuation_layer SET create_date = %s WHERE id=%s',
                    (create_date,stock_valuation.id,)
                )
                category = product_id.categ_id
                debit_account = category.property_stock_valuation_account_id
                credit_account = category.property_stock_account_input_categ_id
                journal = category.property_stock_journal

                if not debit_account or not credit_account:
                    raise UserError(_("Accounts not configured for product category: %s") % category.name)
                account_move = self.env['account.move'].create({
                'journal_id': journal.id,
                'ref': _("Stock Valuation Adjustment for %s") % product_id.name,
                 })

                line_ids = [
                (0, 0, {
                    'move_id': account_move.id,
                    'account_id': credit_account.id,
                    'debit': 0.0,
                    'credit': value,
                    'name': _("Stock Valuation Credit for %s") % product.name,
                    'product_id': product.id,
                    'quantity': quantity,
                }),
                (0, 0, {
                    'move_id': account_move.id,
                    'account_id': debit_account.id,
                    'debit': value,
                    'credit': 0.0,
                    'name': _("Stock Valuation Debit for %s") % product.name,
                    'product_id': product.id,
                    'quantity': quantity,
                }),
                ]
                account_move.sudo().write({'line_ids': line_ids})
                account_move.action_post()

                reference = f'Manual correction {reference_count} -PPTS'
                reference_count += 1
                stock_valuation.write({'account_move_id': account_move.id,'description':reference })
                self.env.cr.execute(
                    'UPDATE account_move SET date = %s WHERE id=%s',
                    (create_date,account_move.id,)
                )

