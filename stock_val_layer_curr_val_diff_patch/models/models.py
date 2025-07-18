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

        res = ValuationLayer.read_group(
            domain_negative,
            ['ids:array_agg(id)', 'create_date:min'],
            ['product_id'],
            orderby='create_date, id'
        )

        min_create_date = datetime.max
        for group in res:
            svls_to_vacuum_by_product[group['product_id'][0]] = ValuationLayer.browse(group['ids'])
            min_create_date = min(min_create_date, group['create_date'])

        all_candidates_by_product = defaultdict(lambda: ValuationLayer)

        domain_positive = [
            ('product_id', 'in', self.ids),
            ('remaining_qty', '>', 0),
            ('company_id', '=', company.id),
            ('create_date', '>=', min_create_date),
        ]
        if cutoff_date:
            domain_positive.append(('create_date', '>=', cutoff_date))

        res = ValuationLayer.read_group(
            domain_positive,
            ['ids:array_agg(id)'],
            ['product_id'],
            orderby='id'
        )

        for group in res:
            all_candidates_by_product[group['product_id'][0]] = ValuationLayer.browse(group['ids'])
