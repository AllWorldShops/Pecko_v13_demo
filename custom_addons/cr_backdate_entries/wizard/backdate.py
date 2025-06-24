# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    def _set_scheduled_date(self):
        """Set move line dates to match the scheduled date of picking"""
        for picking in self:
            picking.move_line_ids.write({'date': picking.scheduled_date})


class BackDateWiz(models.TransientModel):
    _name = 'backdate.entries.wiz'
    _description = "Backdate Wizard"

    date = fields.Datetime('Date', default=fields.Datetime.now)
    picking_ids = fields.Many2many('stock.picking')

    def change_to_backdate_wizard(self):
        """Opens the backdate wizard form view"""
        return {
            'name': 'Backdate Transfer',
            'res_model': 'backdate.entries.wiz',
            'view_mode': 'form',
            'view_id': self.env.ref('cr_backdate_entries.backdate_wizard_view_form').id,
            'target': 'new',
            'type': 'ir.actions.act_window'
        }

    def change_to_backdate(self):
        """Apply backdate changes to stock quants, purchase orders, sales orders, or manufacturing orders."""
        active_model = self._context.get('active_model')
        active_ids = self._context.get('active_ids', [])
        records = self.env[active_model].browse(active_ids)

        if active_model == 'stock.quant':
            for quant in records:
                quant.write({
                    'in_date': self.date,
                    'inventory_date': self.date,
                })

                stock_moves = self.env['stock.move'].search([
                    ('product_id', '=', quant.product_id.id),
                    ('location_dest_id', '=', quant.location_id.id),
                    ('state', '=', 'done')
                ])

                for move in stock_moves:
                    move.write({'date': self.date})
                    move.move_line_ids.write({'date': self.date})

                    for layer in self.env['stock.valuation.layer'].search([('stock_move_id', '=', move.id)]):
                        self.env.cr.execute(
                            'UPDATE stock_valuation_layer SET create_date = %s WHERE id = %s',
                            (self.date, layer.id)
                        )
                        if layer.account_move_id:
                            self.env.cr.execute(
                                'UPDATE account_move SET date = %s, invoice_date = %s WHERE id = %s',
                                (self.date, self.date, layer.account_move_id.id)
                            )
                            self.env.cr.execute(
                                'UPDATE account_move_line SET date = %s WHERE move_id = %s',
                                (self.date, layer.account_move_id.id)
                            )

        elif active_model == 'purchase.order':
            for po in records:
                if po.state not in ['purchase', 'done']:
                    raise UserError(_("Purchase Order must be confirmed or done."))

                po.write({'date_order': self.date})
                po.write({'date_approve': self.date})

                po.order_line.write({'date_planned': self.date})

                for picking in po.picking_ids:
                    if picking.state == 'done':
                        picking.write({'scheduled_date': self.date, 'date_done': self.date})
                        for move in picking.move_ids:
                            move.write({'date': self.date})
                            move.move_line_ids.write({'date': self.date})

                            for layer in self.env['stock.valuation.layer'].search([('stock_move_id', '=', move.id)]):
                                self.env.cr.execute(
                                    'UPDATE stock_valuation_layer SET create_date = %s WHERE id = %s',
                                    (self.date, layer.id)
                                )
                                if layer.account_move_id:
                                    self.env.cr.execute(
                                        'UPDATE account_move SET date = %s, invoice_date = %s WHERE id = %s',
                                        (self.date, self.date, layer.account_move_id.id)
                                    )
                                    self.env.cr.execute(
                                        'UPDATE account_move_line SET date = %s WHERE move_id = %s',
                                        (self.date, layer.account_move_id.id)
                                    )

                            quant_ids = self.env['stock.quant'].search([
                                ('product_id', '=', move.product_id.id),
                                ('location_id', '=', move.location_dest_id.id)
                            ])
                            quant_ids.write({'in_date': self.date})

        elif active_model == 'sale.order':
            for so in records:
                if so.state not in ['sale', 'done']:
                    raise UserError(_("Sales Order must be confirmed or done."))

                so.write({'date_order': self.date})
                so.order_line.write({'commitment_date': self.date})

                for picking in so.picking_ids:
                    if picking.state == 'done':
                        picking.write({'scheduled_date': self.date, 'date_done': self.date})
                        for move in picking.move_ids:
                            move.write({'date': self.date})
                            move.move_line_ids.write({'date': self.date})

                            for layer in self.env['stock.valuation.layer'].search([('stock_move_id', '=', move.id)]):
                                self.env.cr.execute(
                                    'UPDATE stock_valuation_layer SET create_date = %s WHERE id = %s',
                                    (self.date, layer.id)
                                )
                                if layer.account_move_id:
                                    self.env.cr.execute(
                                        'UPDATE account_move SET date = %s, invoice_date = %s WHERE id = %s',
                                        (self.date, self.date, layer.account_move_id.id)
                                    )
                                    self.env.cr.execute(
                                        'UPDATE account_move_line SET date = %s WHERE move_id = %s',
                                        (self.date, layer.account_move_id.id)
                                    )

        elif active_model == 'mrp.production':
            for mo in records:
                if mo.state not in ['done']:
                    raise UserError(_("Only completed Manufacturing Orders can be backdated."))

                mo.write({'date_start': self.date, 'date_finished': self.date})

                for move in mo.move_raw_ids + mo.move_finished_ids:
                    move.write({'date': self.date})
                    move.move_line_ids.write({'date': self.date})

                    for layer in self.env['stock.valuation.layer'].search([('stock_move_id', '=', move.id)]):
                        self.env.cr.execute(
                            'UPDATE stock_valuation_layer SET create_date = %s WHERE id = %s',
                            (self.date, layer.id)
                        )
                        if layer.account_move_id:
                            self.env.cr.execute(
                                'UPDATE account_move SET date = %s, invoice_date = %s WHERE id = %s',
                                (self.date, self.date, layer.account_move_id.id)
                            )
                            self.env.cr.execute(
                                'UPDATE account_move_line SET date = %s WHERE move_id = %s',
                                (self.date, layer.account_move_id.id)
                            )


        elif active_model == 'stock.move.line':

            for line in records:
                if line.state != 'done':
                    raise UserError(_("Only completed Stock Move Lines can be backdated."))
                line.write({'date': self.date})
                move = line.move_id
                if move and move.state == 'done':
                    move.write({'date': self.date})
                    move.move_line_ids.write({'date': self.date})
                    valuation_layers = self.env['stock.valuation.layer'].search([
                        ('stock_move_id', '=', move.id)
                    ])
                    for layer in valuation_layers:
                        self.env.cr.execute(
                            'UPDATE stock_valuation_layer SET create_date = %s WHERE id = %s',
                            (self.date, layer.id)
                        )
                        if layer.account_move_id:
                            self.env.cr.execute(
                                'UPDATE account_move SET date = %s, invoice_date = %s WHERE id = %s',
                                (self.date, self.date, layer.account_move_id.id)
                            )
                            self.env.cr.execute(
                                'UPDATE account_move_line SET date = %s WHERE move_id = %s',
                                (self.date, layer.account_move_id.id)
                            )
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.location_dest_id.id)
                ], limit=1)
                if quant:
                    quant.write({
                        'in_date': self.date,
                        'inventory_date': self.date,
                    })

        else:
            raise UserError(
                _("This wizard only supports stock quant, purchase order, sales order, or manufacturing order."))

        return {'type': 'ir.actions.act_window_close'}

    # def _update_mrp_order(self):
    #     """Update Dates for Manufacturing Order"""
    #     mrp_production_ids = self.env['mrp.production'].browse(self._context.get('active_ids'))
    #     for mrp in mrp_production_ids:
    #         self.env.cr.execute('UPDATE mrp_production SET date_start=%s WHERE id=%s',
    #                             (self.date, mrp.id))
    #         self._update_stock_moves(mrp.all_move_ids)
    #
    # def _update_stock_scrap(self):
    #     """Update Dates for Scrap Stock and related records"""
    #     scrap_stock_ids = self.env['stock.scrap'].browse(self._context.get('active_ids'))
    #     for stock in scrap_stock_ids:
    #         stock.date_done = self.date
    #         self._update_stock_moves(stock.move_ids)
    #
    # def _update_sale_orders(self):
    #     """Update dates for sale orders and related records"""
    #     sale_orders = self.env['sale.order'].browse(self._context.get('active_ids'))
    #     for sale in sale_orders:
    #         sale.date_order = self.date
    #         self._update_pickings(sale.picking_ids)
    #         self._update_invoices(sale.invoice_ids)
    #
    # def _update_purchase_orders(self):
    #     """Update dates for purchase orders and related records"""
    #     purchase_orders = self.env['purchase.order'].browse(self._context.get('active_ids'))
    #     for purchase in purchase_orders:
    #         purchase.date_approve = self.date
    #         purchase.date_order = self.date
    #         self._update_pickings(purchase.picking_ids)
    #         self._update_invoices(purchase.invoice_ids)
    #
    # def _update_stock_quant(self):
    #     """Update inventory date and related stock move records"""
    #     stock_quants = self.env['stock.quant'].browse(self._context.get('active_ids'))
    #     for quant in stock_quants:
    #         quant.inventory_date = self.date
    #         move_lines = self.env['stock.move.line'].search([('quant_id', '=', quant.id)])
    #         self._update_stock_moves(move_lines.mapped('move_id'))
    #
    # def _update_stock_picking(self):
    #     """Update dates for stock pickings"""
    #     pickings = self.env['stock.picking'].browse(self._context.get('active_ids'))
    #     self._update_pickings(pickings)
    #
    # def _update_pickings(self, pickings):
    #     """Update stock picking and related stock moves"""
    #     for picking in pickings:
    #         moves = picking.move_ids
    #         self._update_stock_moves(moves)
    #
    #         picking.write({
    #             'scheduled_date': self.date,
    #             'date_deadline': self.date,
    #             'date_done': self.date,
    #         })
    #
    # def _update_stock_moves(self, moves):
    #     """Update stock moves and related valuation layers"""
    #     for move in moves:
    #         move.write({'date': self.date})
    #
    #         # Update stock valuation layers
    #         valuation_layers = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move.id)])
    #         for layer in valuation_layers:
    #             print(layer,'sssssq2345t')
    #             self.env.cr.execute('UPDATE stock_valuation_layer SET create_date=%s WHERE id=%s',
    #                                 (self.date, layer.id))
    #
    #         # Update stock move lines
    #         move.move_line_ids.write({'date': self.date})
    #
    # def _update_invoices(self, invoices):
    #     """Update account moves (invoices)"""
    #     for invoice in invoices:
    #         if invoice.state == 'draft':
    #             invoice.write({'date': self.date, 'invoice_date': self.date})
    #         elif invoice.state == 'posted':
    #             invoice.button_draft()
    #             invoice.write({'name': False, 'date': self.date, 'invoice_date': self.date})
    #             invoice.action_post()
    #
    #         invoice.invoice_line_ids.write({'date': self.date})
    #         invoice.line_ids.write({'date': self.date})
