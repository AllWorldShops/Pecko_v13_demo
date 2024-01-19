import base64
import csv
from io import StringIO
from odoo import models, fields, _
from datetime import datetime



class ImportStockValuation(models.TransientModel):
    _name = "import.stock.valuation"

    file = fields.Binary(string='File')

    def import_stock_valuation_data(self):
        csv_data = base64.b64decode(self.file)
        csv_string = csv_data.decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_string))
        for row in csv_reader:
            if row:
                create_date = row['Date']
                stock_move = self.env['stock.move'].search([('reference', '=', row['Reference'])],limit=1)
                product = self.env['product.product'].search([('default_code', '=', row['Product'])])
                if product:
                    product_id = product
                quantity = row['Done']
                company_id = self.env['res.company'].search([('name', '=', row['Company'])])
                unit_cost = product_id.standard_price
                value = float(unit_cost) * float(quantity)
                stock_valuation = self.env['stock.valuation.layer'].create({
                    # 'create_date': create_date,
                    'stock_move_id': stock_move.id or False,
                    'product_id': product_id.id or False,
                    'company_id': company_id.id or False,
                    'quantity': quantity,
                    'unit_cost': unit_cost,
                    'value': value

                })

                self.env.cr.execute(
                    'UPDATE stock_valuation_layer SET create_date = %s WHERE id=%s',
                    (create_date,stock_valuation.id,)
                )

