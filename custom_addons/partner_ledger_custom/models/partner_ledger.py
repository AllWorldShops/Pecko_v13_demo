# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, _lt
from datetime import timedelta
from odoo.tools import SQL
from odoo.exceptions import UserError


class AccountPartnerLedgerReportInh(models.AbstractModel):
    _inherit = "account.partner.ledger.report.handler"
    
    @api.model
    def _get_templates(self):
        templates = super(AccountPartnerLedgerReportInh, self)._get_templates()
        templates['line_template'] = 'account_reports.line_template_partner_ledger_report'
        return templates

    ####################################################
    # OPTIONS
    ####################################################

    @api.model
    def _get_options_account_type(self, options):
        ''' Get select account type in the filter widget (see filter_account_type).
        :param options: The report options.
        :return:        Selected account types.
        '''
        all_account_types = []
        account_types = []
        for account_type_option in options.get('account_type', []):
            if account_type_option['selected']:
                account_types.append(account_type_option)
            all_account_types.append(account_type_option)
        return account_types or all_account_types

    @api.model
    def _get_options_domain(self, options):
        # OVERRIDE
        # Handle filter_unreconciled + filter_account_type
        domain = super(AccountPartnerLedgerReportInh, self)._get_options_domain(options)
        if options.get('unreconciled'):
            domain.append(('full_reconcile_id', '=', False))
        domain.append(('account_id.internal_type', 'in', [t['id'] for t in self._get_options_account_type(options)]))

        # Partner must be set.
        domain.append(('partner_id', '!=', False))

        return domain

    @api.model
    def _get_options_sum_balance(self, options):
        ''' Create options with the 'strict_range' enabled on the filter_date.
        The resulting dates domain will be:
        # [
        #     ('date' <= options['date_to']),
        #     ('date' >= options['date_from'])
        # ]
        :param options: The report options.
        :return:        A copy of the options.
        '''
        new_options = options.copy()
        new_options['date'] = new_options['date'].copy()
        new_options['date']['strict_range'] = True
        return new_options

    @api.model
    def _get_options_initial_balance(self, options):
        ''' Create options used to compute the initial balances for each partner.
        The resulting dates domain will be:
        [('date' <= options['date_from'] - 1)]
        :param options: The report options.
        :return:        A copy of the options.
        '''
        new_options = options.copy()
        new_options['date'] = new_options['date'].copy()
        new_date_to = fields.Date.from_string(new_options['date']['date_from']) - timedelta(days=1)
        new_options['date'].update({
            'date_from': False,
            'date_to': fields.Date.to_string(new_date_to),
        })
        return new_options

    ####################################################
    # QUERIES
    ####################################################

    def _get_query_sums(self, report, options):
        """ Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all partners.
        - sums for the initial balances.
        :param options:             The report options.
        :return:                    query as SQL object
        """
        queries = []

        # Create the currency table.
        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            query = report._get_report_query(column_group_options, 'from_beginning')
            queries.append(SQL(
                """
                SELECT
                    account_move_line.partner_id  AS groupby,
                    %(column_group_key)s          AS column_group_key,
                    SUM(%(debit_select)s)         AS debit,
                    SUM(%(credit_select)s)        AS credit,
                    SUM(%(balance_select)s)       AS amount,
                    SUM(%(balance_select)s)       AS balance
                FROM %(table_references)s
                %(currency_table_join)s
                WHERE %(search_condition)s
                GROUP BY account_move_line.partner_id
                """,
                column_group_key=column_group_key,
                debit_select=report._currency_table_apply_rate(SQL("account_move_line.debit")),
                credit_select=report._currency_table_apply_rate(SQL("account_move_line.credit")),
                balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(column_group_options),
                search_condition=query.where_clause,
            ))

        return SQL(' UNION ALL ').join(queries)
    
    def _get_aml_values(self, options, partner_ids, offset=0, limit=None):
        rslt = {partner_id: [] for partner_id in partner_ids}

        partner_ids_wo_none = [x for x in partner_ids if x]
        directly_linked_aml_partner_clauses = []
        indirectly_linked_aml_partner_clause = SQL('aml_with_partner.partner_id IS NOT NULL')
        if None in partner_ids:
            directly_linked_aml_partner_clauses.append(SQL('account_move_line.partner_id IS NULL'))
        if partner_ids_wo_none:
            directly_linked_aml_partner_clauses.append(SQL('account_move_line.partner_id IN %s', tuple(partner_ids_wo_none)))
            indirectly_linked_aml_partner_clause = SQL('aml_with_partner.partner_id IN %s', tuple(partner_ids_wo_none))
        directly_linked_aml_partner_clause = SQL('(%s)', SQL(' OR ').join(directly_linked_aml_partner_clauses))

        queries = []
        journal_name = self.env['account.journal']._field_to_sql('journal', 'name')
        report = self.env.ref('account_reports.partner_ledger_report')
        additional_columns = self._get_additional_column_aml_values()
        for column_group_key, group_options in report._split_options_per_column_group(options).items():
            query = report._get_report_query(group_options, 'strict_range')
            account_alias = query.left_join(lhs_alias='account_move_line', lhs_column='account_id', rhs_table='account_account', rhs_column='id', link='account_id')
            account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)
            account_name = self.env['account.account']._field_to_sql(account_alias, 'name')

            # For the move lines directly linked to this partner
            # ruff: noqa: FURB113
            queries.append(SQL(
                '''
                SELECT
                    account_move_line.id,
                    account_move_line.date_maturity,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    account_move_line.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    account_move_line.matching_number,
                    account_move.customer_po_no, 
                    account_move.ref,    
                    %(additional_columns)s
                    COALESCE(account_move_line.invoice_date, account_move_line.date) AS invoice_date,
                    account_move.customer_po_no AS customer_po_no,
                    %(debit_select)s                                                 AS debit,
                    %(credit_select)s                                                AS credit,
                    %(balance_select)s                                               AS amount,
                    %(balance_select)s                                               AS balance,
                    account_move.name                                                AS move_name,
                    account_move.move_type                                           AS move_type,
                    %(account_code)s                                                 AS account_code,
                    %(account_name)s                                                 AS account_name,
                    journal.code                                                     AS journal_code,
                    %(journal_name)s                                                 AS journal_name,
                    %(column_group_key)s                                             AS column_group_key,
                    'directly_linked_aml'                                            AS key,
                    0                                                                AS partial_id
                FROM %(table_references)s
                JOIN account_move ON account_move.id = account_move_line.move_id
                %(currency_table_join)s
                LEFT JOIN res_company company               ON company.id = account_move_line.company_id
                LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
                LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
                WHERE %(search_condition)s AND %(directly_linked_aml_partner_clause)s
                ORDER BY account_move_line.date, account_move_line.id
                ''',
                additional_columns=additional_columns,
                debit_select=report._currency_table_apply_rate(SQL("account_move_line.debit")),
                credit_select=report._currency_table_apply_rate(SQL("account_move_line.credit")),
                balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                account_code=account_code,
                account_name=account_name,
                journal_name=journal_name,
                column_group_key=column_group_key,
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(group_options),
                search_condition=query.where_clause,
                directly_linked_aml_partner_clause=directly_linked_aml_partner_clause,
            ))

            # For the move lines linked to no partner, but reconciled with this partner. They will appear in grey in the report
            queries.append(SQL(
                '''
                SELECT
                    account_move_line.id,
                    account_move_line.date_maturity,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    aml_with_partner.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    account_move_line.matching_number,
                    account_move.customer_po_no,    
                    account_move.ref, 
                    %(additional_columns)s
                    COALESCE(account_move_line.invoice_date, account_move_line.date) AS invoice_date,
                    account_move.customer_po_no AS customer_po_no,

                    %(debit_select)s                                                 AS debit,
                    %(credit_select)s                                                AS credit,
                    %(balance_select)s                                               AS amount,
                    %(balance_select)s                                               AS balance,
                    account_move.name                                                AS move_name,
                    account_move.move_type                                           AS move_type,
                    %(account_code)s                                                 AS account_code,
                    %(account_name)s                                                 AS account_name,
                    journal.code                                                     AS journal_code,
                    %(journal_name)s                                                 AS journal_name,
                    %(column_group_key)s                                             AS column_group_key,
                    'indirectly_linked_aml'                                          AS key,
                    partial.id                                                       AS partial_id
                FROM %(table_references)s
                    %(currency_table_join)s,
                    account_partial_reconcile partial,
                    account_move,
                    account_move_line aml_with_partner,
                    account_journal journal
                WHERE
                    (account_move_line.id = partial.debit_move_id OR account_move_line.id = partial.credit_move_id)
                    AND account_move_line.partner_id IS NULL
                    AND account_move.id = account_move_line.move_id
                    AND (aml_with_partner.id = partial.debit_move_id OR aml_with_partner.id = partial.credit_move_id)
                    AND %(indirectly_linked_aml_partner_clause)s
                    AND journal.id = account_move_line.journal_id
                    AND %(account_alias)s.id = account_move_line.account_id
                    AND %(search_condition)s
                    AND partial.max_date BETWEEN %(date_from)s AND %(date_to)s
                ORDER BY account_move_line.date, account_move_line.id
                ''',
                additional_columns=additional_columns,
                debit_select=report._currency_table_apply_rate(SQL("CASE WHEN aml_with_partner.balance > 0 THEN 0 ELSE partial.amount END")),
                credit_select=report._currency_table_apply_rate(SQL("CASE WHEN aml_with_partner.balance < 0 THEN 0 ELSE partial.amount END")),
                balance_select=report._currency_table_apply_rate(SQL("-SIGN(aml_with_partner.balance) * partial.amount")),
                account_code=account_code,
                account_name=account_name,
                journal_name=journal_name,
                column_group_key=column_group_key,
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(group_options),
                indirectly_linked_aml_partner_clause=indirectly_linked_aml_partner_clause,
                account_alias=SQL.identifier(account_alias),
                search_condition=query.where_clause,
                date_from=group_options['date']['date_from'],
                date_to=group_options['date']['date_to'],
            ))

        query = SQL(" UNION ALL ").join(SQL("(%s)", query) for query in queries)

        if offset:
            query = SQL('%s OFFSET %s ', query, offset)

        if limit:
            query = SQL('%s LIMIT %s ', query, limit)

        self._cr.execute(query)
        for aml_result in self._cr.dictfetchall():
            if aml_result['key'] == 'indirectly_linked_aml':

                # Append the line to the partner found through the reconciliation.
                if aml_result['partner_id'] in rslt:
                    rslt[aml_result['partner_id']].append(aml_result)

                # Balance it with an additional line in the Unknown Partner section but having reversed amounts.
                if None in rslt:
                    rslt[None].append({
                        **aml_result,
                        'debit': aml_result['credit'],
                        'credit': aml_result['debit'],
                        'amount': aml_result['credit'] - aml_result['debit'],
                        'balance': -aml_result['balance'],
                    })
            else:
                rslt[aml_result['partner_id']].append(aml_result)

        return rslt



    @api.model
    def _do_query(self, options, expanded_partner=None):
        ''' Execute the queries, perform all the computation and return partners_results,
        a lists of tuple (partner, fetched_values) sorted by the table's model _order:
            - partner is a res.parter record.
            - fetched_values is a dictionary containing:
                - sum:                              {'debit': float, 'credit': float, 'balance': float}
                # - (optional) initial_balance:       {'debit': float, 'credit': float, 'balance': float}
                - (optional) lines:                 [line_vals_1, line_vals_2, ...]
        :param options:             The report options.
        :param expanded_account:    An optional account.account record that must be specified when expanding a line
                                    with of without the load more.
        :param fetch_lines:         A flag to fetch the account.move.lines or not (the 'lines' key in accounts_values).
        :return:                    (accounts_values, taxes_results)
        '''
        company_currency = self.env.company.currency_id

        # Execute the queries and dispatch the results.
        query, params = self._get_query_sums(options, expanded_partner=expanded_partner)

        groupby_partners = {}

        self._cr.execute(query, params)
        for res in self._cr.dictfetchall():
            key = res['key']
            if key == 'sum':
                if not company_currency.is_zero(res['debit']) or not company_currency.is_zero(res['credit']):
                    groupby_partners.setdefault(res['groupby'], {})
                    groupby_partners[res['groupby']][key] = res
            elif key == 'initial_balance':
                if not company_currency.is_zero(res['balance']):
                    groupby_partners.setdefault(res['groupby'], {})
                    groupby_partners[res['groupby']][key] = res

        # Fetch the lines of unfolded accounts.
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])
        if expanded_partner or unfold_all or options['unfolded_lines']:
            query, params = self._get_aml_values(options, expanded_partner=expanded_partner)
            self._cr.execute(query, params)
            for res in self._cr.dictfetchall():
                if res['partner_id'] not in groupby_partners:
                    continue
                groupby_partners[res['partner_id']].setdefault('lines', [])
                groupby_partners[res['partner_id']]['lines'].append(res)

        # Retrieve the partners to browse.
        # groupby_partners.keys() contains all account ids affected by:
        # - the amls in the current period.
        # - the amls affecting the initial balance.
        # Note a search is done instead of a browse to preserve the table ordering.
        if expanded_partner:
            partners = expanded_partner
        elif groupby_partners:
            partners = self.env['res.partner'].with_context(active_test=False).search([('id', 'in', list(groupby_partners.keys()))])
        else:
            partners = []
        return [(partner, groupby_partners[partner.id]) for partner in partners]

    ####################################################
    # COLUMNS/LINES
    ####################################################

    @api.model
    def _get_report_line_partner(self, options, partner, initial_balance,debit, credit, balance):
        company_currency = self.env.company.currency_id
        unfold_all = self._context.get('print_mode') and not options.get('unfolded_lines')

        columns = [
            {'name': self.format_value(initial_balance), 'class': 'number'},
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': ''})
        columns.append({'name': self.format_value(balance), 'class': 'number'})

        return {
            'id': 'partner_%s' % partner.id,
            'name': partner.name[:128],
            'columns': columns,
            'level': 2,
            'trust': partner.trust,
            'unfoldable': not company_currency.is_zero(debit) or not company_currency.is_zero(credit),
            'unfolded': 'partner_%s' % partner.id in options['unfolded_lines'] or unfold_all,
            'colspan': 7,
        }

    def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group, level_shift=0):
        if aml_query_result['payment_id']:
            caret_type = 'account.payment'
        else:
            caret_type = 'account.move.line'

        columns = []
        report = self.env['account.report'].browse(options['report_id'])
        for column in options['columns']:
            col_expr_label = column['expression_label']

            if col_expr_label not in aml_query_result:
                raise UserError(_("The column '%s' is not available for this report.", col_expr_label))

            col_value = aml_query_result[col_expr_label] if column['column_group_key'] == aml_query_result['column_group_key'] else None

            if col_value is None:
                columns.append(report._build_column_dict(None, None))
            else:
                currency = False

                if col_expr_label == 'balance':
                    col_value += init_bal_by_col_group[column['column_group_key']]

                if col_expr_label == 'amount_currency':
                    currency = self.env['res.currency'].browse(aml_query_result['currency_id'])

                    if currency == self.env.company.currency_id:
                        col_value = ''

                columns.append(report._build_column_dict(col_value, column, options=options, currency=currency))

        return {
            'id': report._get_generic_line_id('account.move.line', aml_query_result['id'], parent_line_id=partner_line_id, markup=aml_query_result['partial_id']),
            'parent_id': partner_line_id,
            'name': self._format_aml_name(aml_query_result['name'], aml_query_result['ref'], aml_query_result['move_name']),
            'columns': columns,
            'caret_options': caret_type,
            'level': 4 + level_shift,
        }

        

    # def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group):
    #     if aml_query_result['payment_id']:
    #         caret_type = 'account.payment'
    #     else:
    #         caret_type = 'account.move.line'

    #     columns = []
    #     report = self.env['account.report']
    #     for column in options['columns']:
    #         col_expr_label = column['expression_label']
    #         if col_expr_label == 'ref':
    #             col_value = report._format_aml_name(aml_query_result['name'], aml_query_result['ref'], aml_query_result['move_name'])
    #         else:
    #             col_value = aml_query_result[col_expr_label] if column['column_group_key'] == aml_query_result['column_group_key'] else None

    #         if col_value is None:
    #             columns.append({})
    #         else:
    #             col_class = 'number'

    #             if col_expr_label == 'date_maturity':
    #                 formatted_value = format_date(self.env, fields.Date.from_string(col_value))
    #                 col_class = 'date'
    #             elif col_expr_label == 'amount_currency':
    #                 currency = self.env['res.currency'].browse(aml_query_result['currency_id'])
    #                 formatted_value = report.format_value(col_value, currency=currency, figure_type=column['figure_type'])
    #             elif col_expr_label == 'balance':
    #                 col_value += init_bal_by_col_group[column['column_group_key']]
    #                 formatted_value = report.format_value(col_value, figure_type=column['figure_type'], blank_if_zero=column['blank_if_zero'])
    #             else:
    #                 if col_expr_label == 'ref':
    #                     col_class = 'o_account_report_line_ellipsis'
    #                 elif col_expr_label not in ('debit', 'credit'):
    #                     col_class = ''
    #                 formatted_value = report.format_value(col_value, figure_type=column['figure_type'])

    #             columns.append({
    #                 'name': formatted_value,
    #                 'no_format': col_value,
    #                 'class': col_class,
    #             })

    #     return {
    #         'id': report._get_generic_line_id('account.move.line', aml_query_result['id'], parent_line_id=partner_line_id),
    #         'parent_id': partner_line_id,
    #         'name': format_date(self.env, aml_query_result['date']),
    #         'class': 'text-muted' if aml_query_result['key'] == 'indirectly_linked_aml' else 'text',  # do not format as date to prevent text centering
    #         'columns': columns,
    #         'caret_options': caret_type,
    #         'level': 2,
    #     }

    # @api.model
    # def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group):
        
    #     report = self.env['account.report']
    #     if aml_query_result['payment_id']:
    #         caret_type = 'account.payment'
    #     elif aml_query_result['move_type'] in ('in_refund', 'in_invoice', 'in_receipt'):
    #         caret_type = 'account.invoice.in'
    #     elif aml_query_result['move_type'] in ('out_refund', 'out_invoice', 'out_receipt'):
    #         caret_type = 'account.invoice.out'
    #     else:
    #         caret_type = 'account.move'

    #     date_maturity = aml_query_result['date_maturity'] and format_date(self.env, fields.Date.from_string(aml_query_result['date_maturity']))
    #     columns = [
    #         {'name': aml_query_result['journal_code']},
    #         {'name': aml_query_result['account_code']},
    #         {'name': aml_query_result['customer_po_no'] or ''},
    #         {'name': report._format_aml_name(aml_query_result['name'], aml_query_result['ref'], aml_query_result['move_name'])},
    #         {'name': date_maturity or '', 'class': 'date'},
    #         # {'name': aml['full_rec_name'] or ''},
    #         # {'name': report.format_value(cumulated_init_balance), 'class': 'number'},
    #         {'name': report.format_value(aml_query_result['debit'], blank_if_zero=True), 'class': 'number'},
    #         {'name': report.format_value(aml_query_result['credit'], blank_if_zero=True), 'class': 'number'},
    #     ]
    #     print('columns----------',columns)
    #     if self.user_has_groups('base.group_multi_currency'):
    #         report = self.env['account.report']
    #         if aml_query_result['currency_id']:
    #             currency = report.env['res.currency'].browse(aml_query_result['currency_id'])
    #             formatted_amount = report.format_value(aml_query_result['amount_currency'], currency=currency, blank_if_zero=True)
    #             columns.append({'name': formatted_amount, 'class': 'number'})
    #         else:
    #             columns.append({'name': ''})
    #     # columns.append({'name': report.format_value(cumulated_balance), 'class': 'number'})
    #     return {
    #         'id': report._get_generic_line_id('account.move.line', aml_query_result['id'], parent_line_id=partner_line_id),
    #         'parent_id': partner_line_id,
    #         'name': format_date(self.env, aml_query_result['date']),
    #         'class': 'date',
    #         'columns': columns,
    #         'caret_options': caret_type,
    #         'level': 4,
    #     }

    @api.model
    def _get_report_line_load_more(self, options, partner, offset, remaining, progress):
        return {
            'id': 'loadmore_%s' % partner.id,
            'offset': offset,
            'progress': progress,
            'remaining': remaining,
            'class': 'o_account_reports_load_more text-center',
            'parent_id': 'account_%s' % partner.id,
            'name': _('Load more... (%s remaining)' % remaining),
            'colspan': 10 if self.user_has_groups('base.group_multi_currency') else 9,
            'columns': [{}],
        }

    # @api.model
    # def _get_report_line_total(self, options, totals_by_column_group):
    #     report = self.env['account.report']
    #     columns = [
    #         {'name': report.format_value(balance), 'class': 'number'},
    #         {'name': report.format_value(debit), 'class': 'number'},
    #         {'name': report.format_value(credit), 'class': 'number'},
    #     ]
    #     if self.user_has_groups('base.group_multi_currency'):
    #         columns.append({'name': ''})
    #     columns.append({'name': report.format_value(balance), 'class': 'number'})
    #     return {
    #         'id': 'partner_ledger_total_%s' % self.env.company.id,
    #         'name': _('Total'),
    #         'class': 'total',
    #         'level': 1,
    #         'columns': columns,
    #         'colspan': 7,
    #     }

    def _get_report_line_total(self, options, totals_by_column_group):
        column_values = []
        report = self.env['account.report'].browse(options['report_id'])
        for column in options['columns']:
            col_value = totals_by_column_group[column['column_group_key']].get(column['expression_label'])
            column_values.append(report._build_column_dict(col_value, column, options=options))

        return {
            'id': report._get_generic_line_id(None, None, markup='total'),
            'name': _('Total'),
            'level': 1,
            'columns': column_values,
        }

    @api.model
    def _get_partner_ledger_lines(self, options, line_id=None):
        ''' Get lines for the whole report or for a specific line.
        :param options: The report options.
        :return:        A list of lines, each one represented by a dictionary.
        '''
        lines = []
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        expanded_partner = line_id and self.env['res.partner'].browse(int(line_id[8:]))
        partners_results = self._do_query(options, expanded_partner=expanded_partner)

        total_initial_balance = total_debit = total_credit = total_balance = 0.0
        for partner, results in partners_results:
            is_unfolded = 'partner_%s' % partner.id in options['unfolded_lines']

            # res.partner record line.
            partner_sum = results.get('sum', {})
            partner_init_bal = results.get('initial_balance', {})

            initial_balance = partner_init_bal.get('balance', 0.0)
            debit = partner_sum.get('debit', 0.0)
            credit = partner_sum.get('credit', 0.0)
            balance = initial_balance + partner_sum.get('balance', 0.0)

            lines.append(self._get_report_line_partner(options, partner, initial_balance, debit, credit, balance))

            total_initial_balance += initial_balance
            total_debit += debit
            total_credit += credit
            total_balance += balance

            if unfold_all or is_unfolded:
                cumulated_balance = initial_balance

                # account.move.line record lines.
                amls = results.get('lines', [])

                load_more_remaining = len(amls)
                load_more_counter = self._context.get('print_mode') and load_more_remaining or self.MAX_LINES

                for aml_query_result in amls:
                    # Don't show more line than load_more_counter.
                    if load_more_counter == 0:
                        break

                    # cumulated_init_balance = cumulated_balance
                    # cumulated_balance += aml['balance']
                    # lines.append(self._get_report_line_move_line(options, partner, aml, cumulated_init_balance, cumulated_balance))

                    load_more_remaining -= 1
                    load_more_counter -= 1

                if load_more_remaining > 0:
                    # Load more line.
                    lines.append(self._get_report_line_load_more(
                        options,
                        partner,
                        self.MAX_LINES,
                        load_more_remaining,
                        cumulated_balance,
                    ))

        if not line_id:
            # Report total line.
            lines.append(self._get_report_line_total(
                options,
                total_initial_balance,
                total_debit,
                total_credit,
                total_balance
            ))
        return lines

    @api.model
    def _load_more_lines(self, options, line_id, offset, load_more_remaining, progress):
        ''' Get lines for an expanded line using the load more.
        :param options: The report options.
        :return:        A list of lines, each one represented by a dictionary.
        '''
        lines = []

        expanded_partner = line_id and self.env['res.partner'].browse(int(line_id[9:]))

        load_more_counter = self.MAX_LINES

        # Fetch the next batch of lines.
        amls_query, amls_params = self._get_aml_values(options, expanded_partner=expanded_partner, offset=offset, limit=load_more_counter)
        self._cr.execute(amls_query, amls_params)
        for aml_query_result in self._cr.dictfetchall():
            # Don't show more line than load_more_counter.
            if load_more_counter == 0:
                break

            # cumulated_init_balance = progress
            # progress += aml['balance']

            # account.move.line record line.
            # lines.append(self._get_report_line_move_line(options, expanded_partner, aml, cumulated_init_balance, progress))

            offset += 1
            load_more_remaining -= 1
            load_more_counter -= 1

        if load_more_remaining > 0:
            # Load more line.
            lines.append(self._get_report_line_load_more(
                options,
                expanded_partner,
                offset,
                load_more_remaining,
                progress,
            ))
        return lines

    def _get_columns_name(self, options):
        columns = [
            {},
            {'name': _('JRNL')},
            {'name': _('Account')},
            {'name': _('Customer PO No.')},
            {'name': _('Ref')},
            {'name': _('Due Date'), 'class': 'date'},
            {'name': _('Matching Number')},
            {'name': _('Initial Balance'), 'class': 'number'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'}]

        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': _('Amount Currency'), 'class': 'number'})

        columns.append({'name': _('Balance'), 'class': 'number'})

        return columns

    @api.model
    def _get_lines(self, options, line_id=None):
        offset = int(options.get('lines_offset', 0))
        remaining = int(options.get('lines_remaining', 0))
        balance_progress = float(options.get('lines_progress', 0))

        if offset > 0:
            # Case a line is expanded using the load more.
            return self._load_more_lines(options, line_id, offset, remaining, balance_progress)
        else:
            # Case the whole report is loaded or a line is expanded for the first time.
            return self._get_partner_ledger_lines(options, line_id=line_id)

    @api.model
    def _get_report_name(self):
        return _('Partner Ledger')




    # @api.model
    # def _get_query_amls(self, options, expanded_partner=None, offset=None, limit=None):
    #     ''' Construct a query retrieving the account.move.lines when expanding a report line with or without the load
    #     more.
    #     :param options:             The report options.
    #     :param expanded_partner:    The res.partner record corresponding to the expanded line.
    #     :param offset:              The offset of the query (used by the load more).
    #     :param limit:               The limit of the query (used by the load more).
    #     :return:                    (query, params)
    #     '''
    #     unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])
    #
    #     # Get sums for the account move lines.
    #     # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
    #     if expanded_partner:
    #         domain = [('partner_id', '=', expanded_partner.id)]
    #     elif unfold_all:
    #         domain = []
    #     elif options['unfolded_lines']:
    #         domain = [('partner_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]
    #
    #     new_options = self._get_options_sum_balance(options)
    #     tables, where_clause, where_params = self._query_get(new_options, domain=domain)
    #     ct_query = self._get_query_currency_table(options)
    #
    #     query = '''
    #         SELECT
    #             account_move_line.id,
    #             account_move_line.date,
    #             account_move_line.date_maturity,
    #             account_move_line.name,
    #             account_move_line.ref,
    #             account_move_line.company_id,
    #             account_move_line.account_id,
    #             account_move_line.payment_id,
    #             account_move_line.partner_id,
    #             account_move_line.currency_id,
    #             account_move_line.amount_currency,
    #             ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)  AS debit,
    #             ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
    #             ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
    #             account_move_line__move_id.name         AS move_name,
    #             company.currency_id                     AS company_currency_id,
    #             partner.name                            AS partner_name,
    #             account_move_line__move_id.type         AS move_type,
    #             account.code                            AS account_code,
    #             account_move_line__move_id.customer_po_no         AS customer_po_no,
    #             account.name                            AS account_name,
    #             journal.code                            AS journal_code,
    #             journal.name                            AS journal_name,
    #             full_rec.name                           AS full_rec_name
    #         FROM account_move_line
    #         LEFT JOIN account_move account_move_line__move_id ON account_move_line__move_id.id = account_move_line.move_id
    #         LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
    #         LEFT JOIN res_company company               ON company.id = account_move_line.company_id
    #         LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
    #         LEFT JOIN account_account account           ON account.id = account_move_line.account_id
    #         LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
    #         LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
    #         WHERE %s
    #         ORDER BY account_move_line.id
    #     ''' % (ct_query, where_clause)
    #
    #     if offset:
    #         query += ' OFFSET %s '
    #         where_params.append(offset)
    #     if limit:
    #         query += ' LIMIT %s '
    #         where_params.append(limit)
    #
    #     return query, where_params
    #
    # @api.model
    # def _get_report_line_move_line(self, options, partner, aml, cumulated_init_balance, cumulated_balance):
    #     if aml['payment_id']:
    #         caret_type = 'account.payment'
    #     elif aml['move_type'] in ('in_refund', 'in_invoice', 'in_receipt'):
    #         caret_type = 'account.invoice.in'
    #     elif aml['move_type'] in ('out_refund', 'out_invoice', 'out_receipt'):
    #         caret_type = 'account.invoice.out'
    #     else:
    #         caret_type = 'account.move'
    #
    #     date_maturity = aml['date_maturity'] and format_date(self.env, fields.Date.from_string(aml['date_maturity']))
    #     columns = [
    #         {'name': aml['journal_code']},
    #         {'name': aml['account_code']},
    #         {'name': self._format_aml_name(aml['name'], aml['ref'], aml['move_name'])},
    #         {'name': aml['customer_po_no'] or ''},
    #         {'name': date_maturity or '', 'class': 'date'},
    #         {'name': aml['full_rec_name'] or ''},
    #         {'name': self.format_value(cumulated_init_balance), 'class': 'number'},
    #         {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
    #         {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
    #     ]
    #     if self.user_has_groups('base.group_multi_currency'):
    #         if aml['currency_id']:
    #             currency = self.env['res.currency'].browse(aml['currency_id'])
    #             formatted_amount = self.format_value(aml['amount_currency'], currency=currency, blank_if_zero=True)
    #             columns.append({'name': formatted_amount, 'class': 'number'})
    #         else:
    #             columns.append({'name': ''})
    #     columns.append({'name': self.format_value(cumulated_balance), 'class': 'number'})
    #     return {
    #         'id': aml['id'],
    #         'parent_id': 'partner_%s' % partner.id,
    #         'name': format_date(self.env, aml['date']),
    #         'class': 'date',
    #         'columns': columns,
    #         'caret_options': caret_type,
    #         'level': 4,
    #     }

    # @api.model
    # def _get_report_line_partner(self, options, partner, initial_balance, debit, credit, balance):
    #     company_currency = self.env.company.currency_id
    #     unfold_all = self._context.get('print_mode') and not options.get('unfolded_lines')
    #     columns = [
    #         {'name': ' ', 'class': 'number'},
    #         {'name': self.format_value(initial_balance), 'class': 'number'},
    #         {'name': self.format_value(debit), 'class': 'number'},
    #         {'name': self.format_value(credit), 'class': 'number'},
    #     ]
    #     if self.user_has_groups('base.group_multi_currency'):
    #         columns.append({'name': ''})
    #     columns.append({'name': self.format_value(balance), 'class': 'number'})
    #     print(partner, "---++++++++++++", partner.id)
    #     return {
    #         'id': 'partner_%s' % partner.id or False,
    #         'name': partner.name[:128],
    #         'columns': columns,
    #         'level': 2,
    #         'trust': partner.trust,
    #         'unfoldable': not company_currency.is_zero(debit) or not company_currency.is_zero(credit),
    #         'unfolded': 'partner_%s' % partner.id in options['unfolded_lines'] or unfold_all,
    #         'colspan': 6,
    #     }

    # @api.model
    # def _get_report_line_total(self, options, initial_balance, debit, credit, balance):
    #     columns = [
    #         {'name': ' ', 'class': 'number'},
    #         {'name': self.format_value(initial_balance), 'class': 'number'},
    #         {'name': self.format_value(debit), 'class': 'number'},
    #         {'name': self.format_value(credit), 'class': 'number'},
    #     ]
    #     if self.user_has_groups('base.group_multi_currency'):
    #         columns.append({'name': ''})
    #     columns.append({'name': self.format_value(balance), 'class': 'number'})
    #     return {
    #         'id': 'partner_ledger_total_%s' % self.env.company.id,
    #         'name': _('Total'),
    #         'class': 'total',
    #         'level': 1,
    #         'columns': columns,
    #         'colspan': 7,
    #     }
    #
    # def _get_columns_name(self, options):
    #     columns = [
    #         {},
    #         {'name': _('JRNL')},
    #         {'name': _('Account')},
    #         {'name': _('Ref')},
    #         {'name': _('Customer PO No.')},
    #         {'name': _('Due Date'), 'class': 'date'},
    #         {'name': _('Matching Number')},
    #         {'name': _('Initial Balance'), 'class': 'number'},
    #         {'name': _('Debit'), 'class': 'number'},
    #         {'name': _('Credit'), 'class': 'number'}]
    #
    #     if self.user_has_groups('base.group_multi_currency'):
    #         columns.append({'name': _('Amount Currency'), 'class': 'number'})
    #
    #     columns.append({'name': _('Balance'), 'class': 'number'})
    #
    #     return columns



