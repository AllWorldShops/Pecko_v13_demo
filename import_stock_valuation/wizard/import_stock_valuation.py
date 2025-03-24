import base64
import csv
from io import StringIO
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
        if not self.file:
            raise UserError("Please upload a valid CSV file.")

        csv_data = base64.b64decode(self.file)
        csv_string = csv_data.decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_string))
        reference_count = 1
        completed_count = 0
        date_end = datetime.strptime('2024-12-31', '%Y-%m-%d')
        date_start = datetime.strptime('2024-01-01', '%Y-%m-%d')

        for row in csv_reader:
            if not row.get('Date') or not row.get('Product'):
                raise UserError("Missing required fields in CSV.")

            create_date = datetime.strptime(row['Date'], '%Y-%m-%d')
            product = self.env['product.product'].search([('default_code', '=', row['Product'])], limit=1)

            if not product.active:
                _logger.warning("Active Product not found: %s", row['Product'])
                continue
            elif not product :
                raise UserError(_("Product not found: %s") % row['Product'])


            existing_valuation = self.env['stock.valuation.layer'].search([
                ('product_id', '=', product.id),
                ('create_date', '=', create_date),
                ('company_id', '=', self.env.company.id)
            ], limit=1)

            if existing_valuation and existing_valuation.account_move_id:
                _logger.warning(
                    "Valuation and journal entry already exist for product: %s on date: %s. Skipping record.",
                    product.name, create_date)
                continue

            elif existing_valuation:
                _logger.warning("Valuation already exists for product: %s on date: %s. Skipping record.",
                                product.name, create_date)
                continue

            elif self.env['account.move'].search([
                ('ref', 'ilike', f"Stock Valuation Adjustment for {product.name}"),
                ('date', '=', create_date),
                ('journal_id', '=', product.categ_id.property_stock_journal.id)
            ], limit=1):
                _logger.warning("Account move already exists for product: %s on date: %s. Skipping record.",
                                product.name, create_date)
                continue

            stock_moves = self.env['stock.move'].search([
                ('product_id', '=', product.id),
                ('location_dest_id.usage', '=', 'production'),
                ('location_id.usage', 'in', ['internal', 'production']),
                ('state', '=', 'done'),
                ('date', '>=', date_start),
                ('date', '<=', date_end),
                ('company_id', '=', self.env.company.id),
                ('stock_valuation_layer_ids', '=', False)
            ])

            if not stock_moves:
                _logger.warning("No stock moves found for product: %s", product.display_name)
                continue

            total_qty = sum(stock_moves.mapped('product_uom_qty'))
            if total_qty == 0:
                raise UserError(_("Total quantity is zero for product: %s") % product.default_code)

            valuation_layers = self.env['stock.valuation.layer'].search([
                ('product_id', '=', product.id),
                ('create_date', '>=', date_start),
                ('create_date', '<=', date_end),
                ('company_id', '=', self.env.company.id),
                ('stock_move_id.location_id.usage', '=', 'supplier')
            ])

            if not valuation_layers:
                # Get the last valuation layer before the start date
                last_layer = self.env['stock.valuation.layer'].search([
                    ('product_id', '=', product.id),
                    ('company_id', '=', self.env.company.id),
                ], order='create_date desc', limit=1)

            if valuation_layers:
                unit_cost = sum(valuation_layers.mapped('value'))
            else:
                unit_cost = sum(last_layer.mapped('value')) if last_layer else product.standard_price

            re_valuation_layers = self.env['stock.valuation.layer'].search([
                ('product_id', '=', product.id),
                ('create_date', '>=', date_start),
                ('create_date', '<=', date_end),
                ('company_id', '=', self.env.company.id),
                ('stock_move_id.location_id.usage', '=', 'internal'),
                ('stock_move_id.location_dest_id.usage', '=', 'supplier')
            ])
            if re_valuation_layers:
                for rec in re_valuation_layers:
                    matching_layer = next((res for res in rec
                                           if res.stock_move_id
                                           and res.stock_move_id.location_id.usage == 'internal'
                                           and res.stock_move_id.location_dest_id.usage == 'supplier'), None)
                    if matching_layer:
                        unit_cost += matching_layer.value

                # Calculate average unit cost and total value
                average_unit_cost = unit_cost / total_qty if total_qty else 0
                total_value = average_unit_cost * total_qty
            else:
                average_unit_cost = unit_cost / total_qty if total_qty else 0
                total_value = average_unit_cost * total_qty

            stock_valuation = self.env['stock.valuation.layer'].create({
                'create_date': create_date,
                'product_id': product.id,
                'company_id': self.env.company.id,
                'quantity': -1 * total_qty,
                'unit_cost': abs(average_unit_cost),
                'value': -1 * total_value,
            })
            _logger.info("Layer created for %s", product.name)
            self.env.cr.execute('UPDATE stock_valuation_layer SET create_date = %s WHERE id=%s',
                                (create_date, stock_valuation.id,))



            category = product.categ_id
            if not (
                    category.property_stock_valuation_account_id and category.property_stock_account_input_categ_id and category.property_stock_journal):
                raise UserError(_("Accounts or journal not configured for product category: %s") % category.name)

            account_move = self.env['account.move'].create({
                'journal_id': category.property_stock_journal.id,
                'ref': _(f"Stock Valuation Adjustment for {product.name}"),
            })

            account_move.write({'line_ids': [
                (0, 0,
                 {'account_id': category.property_stock_account_input_categ_id.id, 'credit': total_value, 'debit': 0.0,
                  'name': f"Stock Valuation Credit for {product.name}", 'product_id': product.id,
                  'quantity': total_qty}),
                (0, 0,
                 {'account_id': category.property_stock_valuation_account_id.id, 'debit': total_value, 'credit': 0.0,
                  'name': f"Stock Valuation Debit for {product.name}", 'product_id': product.id, 'quantity': total_qty})
            ]})

            account_move.action_post()
            stock_valuation.write(
                {'account_move_id': account_move.id, 'description': f'Manual correction RM {reference_count} -PPTS'})
            reference_count += 1
            completed_count += 1
            _logger.info("Journal Entry created and posted for %s", product.name)

        _logger.info("Stock Valuation Import Process Completed Successfully. Total Records Processed: %s",
                     completed_count)

    # def import_stock_valuation_data(self):
    #     csv_data = base64.b64decode(self.file)
    #     csv_string = csv_data.decode('utf-8')
    #     csv_reader = csv.DictReader(StringIO(csv_string))
    #     reference_count = 1
    #     for row in csv_reader:
    #         if row:
    #             create_date = row['Date']
    #             date_val= date.today()
    #             # stock_move = self.env['stock.move'].search([('reference', '=', row['Reference'])],limit=1)
    #             product = self.env['product.product'].search(
    #             [ '|', ('active', '=', True), ('active', '=', False), ('default_code', '=', row['Product'])], limit=1)
    #             _logger.info("%s product", product.name)
    # 
    #             if not product:
    #                 raise UserError(_("Product not found: %s") % row['Product'])
    # 
    #             on_hand_check= product.with_context({'to_date': date_val}).qty_available
    #             _logger.debug("%s on_hand_check", on_hand_check)
    #             # if on_hand_check == 0.0:
    #             #     _logger.info("%s =======", on_hand_check)
    #             #     continue
    #             if product:
    #                 product_id = product
    #             quantity = row['Done']
    #             company_id = self.env['res.company'].search([('name', '=', row['Company'])])
    #             unit_cost = row['Unit Cost']
    #             # unit_cost = product_id.standard_price
    #             value = row['Total Value']
    # 
    #             stock_valuation = self.env['stock.valuation.layer'].create({
    #                 'create_date': create_date,
    #                 # 'stock_move_id': stock_move.id or False,
    #                 'product_id': product_id.id or False,
    #                 'company_id': company_id.id or False,
    #                 'quantity': quantity,
    #                 'unit_cost': unit_cost,
    #                 'value': value,
    # 
    #             })
    #             _logger.info("%s stock_valuation", stock_valuation)
    # 
    #             self.env.cr.execute(
    #                 'UPDATE stock_valuation_layer SET create_date = %s WHERE id=%s',
    #                 (create_date,stock_valuation.id,)
    #             )
    #             category = product_id.categ_id
    #             debit_account = category.property_stock_valuation_account_id
    #             credit_account = category.property_stock_account_input_categ_id
    #             journal = category.property_stock_journal
    # 
    #             if not debit_account or not credit_account:
    #                 raise UserError(_("Accounts not configured for product category: %s") % category.name)
    #             account_move = self.env['account.move'].create({
    #             'journal_id': journal.id,
    #             'ref': _("Stock Valuation Adjustment for %s") % product_id.name,
    #              })
    # 
    #             line_ids = [
    #             (0, 0, {
    #                 'move_id': account_move.id,
    #                 'account_id': credit_account.id,
    #                 'debit': 0.0,
    #                 'credit': stock_valuation.value,
    #                 'name': _("Stock Valuation Credit for %s") % product.name,
    #                 'product_id': product.id,
    #                 'quantity': quantity,
    #             }),
    #             (0, 0, {
    #                 'move_id': account_move.id,
    #                 'account_id': debit_account.id,
    #                 'debit': stock_valuation.value,
    #                 'credit': 0.0,
    #                 'name': _("Stock Valuation Debit for %s") % product.name,
    #                 'product_id': product.id,
    #                 'quantity': quantity,
    #             }),
    #             ]
    #             account_move.sudo().write({'line_ids': line_ids})
    #             account_move.action_post()
    # 
    #             reference = f'Manual correction {reference_count} -PPTS'
    #             reference_count += 1
    #             stock_valuation.write({'account_move_id': account_move.id,'description':reference })
    #             self.env.cr.execute(
    #                 'UPDATE account_move SET date = %s WHERE id=%s',
    #                 (create_date,account_move.id,)
    #             )
    # 
