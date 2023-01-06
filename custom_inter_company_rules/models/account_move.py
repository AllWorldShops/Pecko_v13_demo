# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _inter_company_create_invoices(self, company):
        ''' Create cross company invoices.
        :param company: The targeted new company (res.company record).
        :return:        The newly created invoices.
        '''
        if self.company_id.id in company.allowed_company_ids.ids:
            invoices_ctx = self.with_user(company.intercompany_user_id).with_context(default_company_id=company.id)
            
            # Prepare invoice values.
            invoices_vals_per_type = {}
            inverse_types = {
                'in_invoice': 'out_invoice',
                'in_refund': 'out_refund',
                'out_invoice': 'in_invoice',
                'out_refund': 'in_refund',
            }
            for inv in invoices_ctx:
                
                invoice_vals = inv._inter_company_prepare_invoice_data(company, inverse_types[inv.type])
                invoice_vals['invoice_line_ids'] = []
                for line in inv.invoice_line_ids:
                    invoice_vals['invoice_line_ids'].append((0, 0, line._inter_company_prepare_invoice_line_data(company)))

                inv_new = inv.new(invoice_vals)
                for line in inv_new.invoice_line_ids:
                    line.tax_ids = line._get_computed_taxes()
                invoice_vals = inv_new._convert_to_write(inv_new._cache)
                invoice_vals.pop('line_ids', None)

                invoices_vals_per_type.setdefault(invoice_vals['type'], [])
                invoices_vals_per_type[invoice_vals['type']].append(invoice_vals)

            # Create invoices.
            moves = None
            for invoice_type, invoices_vals in invoices_vals_per_type.items():
                invoices = invoices_ctx.with_context(default_type=invoice_type).create(invoices_vals)
                if moves:
                    moves += invoices
                else:
                    moves = invoices
            return moves


