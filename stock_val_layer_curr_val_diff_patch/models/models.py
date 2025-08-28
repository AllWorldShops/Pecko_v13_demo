# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime
from collections import defaultdict

class ResCompany(models.Model):
    _inherit = 'res.company'

    stock_valuation_cutoff_datetime = fields.Datetime(string="Stock Valuation Cut-off Date/Time")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _run_fifo_vacuum(self, company=None):
        """Compensate layer valued at an estimated price with the price of future receipts
        if any. If the estimated price is equals to the real price, no layer is created but
        the original layer is marked as compensated.

        :param company: recordset of `res.company` to limit the execution of the vacuum
        """
        if company is None:
            company = self.env.company

        cutoff_date = company.stock_valuation_cutoff_datetime
        ValuationLayer = self.env['stock.valuation.layer'].sudo()
        svls_to_vacuum_by_product = defaultdict(lambda: ValuationLayer)

        domain_negative = [
            ('product_id', 'in', self.ids),
            ('remaining_qty', '<', 0),
            ('stock_move_id', '!=', False),
            ('company_id', '=', company.id),
        ]
        if cutoff_date:
            domain_negative.append(('create_date', '>=', cutoff_date))


        res = ValuationLayer._read_group(domain_negative,
               ['product_id'], ['id:recordset', 'create_date:min'], order='create_date:min')
        min_create_date = datetime.max
        if not res:
            return
        for group in res:
            svls_to_vacuum_by_product[group[0].id] = group[1].sorted(key=lambda r: (r.create_date, r.id))
            min_create_date = min(min_create_date, group[2])

        all_candidates_by_product = defaultdict(lambda: ValuationLayer)

        domain_positive = [
            ('product_id', 'in', self.ids),
            ('remaining_qty', '>', 0),
            ('company_id', '=', company.id),
            ('create_date', '>=', min_create_date),
        ]
        if cutoff_date:
            domain_positive.append(('create_date', '>=', cutoff_date))

        res = ValuationLayer._read_group(domain_positive,
              ['product_id'], ['id:recordset'])

        for group in res:
            all_candidates_by_product[group[0].id] = group[1]