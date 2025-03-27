# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.tools.misc import format_date
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):   
    _inherit = "sale.order"

    def _action_confirm_orders(self):
        sale = self.sudo().search([('origin', '=', 'Activate-'),('state', '=', 'draft'), ('company_id', '=', 1)], limit=500)
        _logger.info("---------Sales Length ----------: %s", str(len(sale)))
        for rec in sale:
            rec.with_delay().action_confirm()

    def _action_confirm_orders_without_delay(self):
        sale = self.sudo().search([('origin', '=', 'Activate-'),('state', '=', 'draft'), ('company_id', '=', 1)], limit=30)
        for rec in sale:
            rec.action_confirm()
            self.env.cr.commit()
        _logger.info("---------+++Confirm sales orders done+++---------")

    attn = fields.Many2one('res.partner',string="ATTN")
    customer_po_no = fields.Char(string="Customer PO No")
    customer_po_date = fields.Date(string="Customer PO Date")
    origin = fields.Char(string='Order Ref No', help="Reference of the document that generated this sales order request.")
    effective_date = fields.Date("Effective Date", compute='_compute_effective_date', store=True, help="Completion date of the first delivery order.")
     
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            for picking in rec.picking_ids:
                picking.write({'attn': self.attn.id,
                                'customer_po_no' :self.customer_po_no})
        for loop in rec.picking_ids:
            for move in loop.move_ids_without_package:
                move.customer_part_no = move.product_id.name
        for line in self.order_line:
            do_moves = self.env['stock.move'].search([('sale_line_id', '=', line.id),('product_id', '=', line.product_id.id)], limit=1)
            if do_moves:
                for obj in do_moves.move_orig_ids:
                    if obj.group_id.name != do_moves.origin:
                        line.mo_reference = obj.group_id.name
        return res


    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['attn'] = self.attn.id
        invoice_vals['customer_po_no'] = self.customer_po_no
        return invoice_vals
    
class SaleOrderLine(models.Model):   
    _inherit = "sale.order.line"
    
    customer_part_no = fields.Text(string='Customer Part No')
    need_date = fields.Date(string="Need Date")
    line_no = fields.Integer(string='Position', default=False)
    requested_date_line = fields.Date(string="Requested Date")
    order_ref = fields.Char('Order Reference',related='order_id.name', store=True)   
    customer_id = fields.Many2one('res.partner',related='order_id.partner_id')
    sales_person_id = fields.Many2one('res.users',related='order_id.user_id')
    promise_date = fields.Datetime('Promised Date',related='order_id.commitment_date')
    promised_date = fields.Date(string="Promised Date")
    customer_po_no = fields.Char('Customer Po No', related='order_id.customer_po_no')   
    internal_ref_no = fields.Char('Internal Ref No',related='product_id.default_code') 
    back_order_qty = fields.Float(string='Pending Qty', compute='_compute_back_order_qty', store=True)
    production_type = fields.Selection([('purchase','Purchased'),('manufacture', 'Manufactured')], string="Purchased / Manufactured")
    mo_reference = fields.Char("M.O Reference")
    do_reference = fields.Char("D.O Reference", compute="_compute_do_reference", store=True)
    need_date = fields.Date(string="Need Date")
    total_invoice_qty = fields.Float(string="Total Invoice", compute='_compute_total_invoice_qty',)

    def _compute_total_invoice_qty(self):
        for line in self:
            line.total_invoice_qty = line.price_unit * line.qty_invoiced if line.qty_invoiced else 0.0

    @api.depends('order_id.picking_ids')
    def _compute_do_reference(self):
        # picking = self.order_id.picking_ids.filtered(lambda l: l.state not in ['done', 'cancel']).sorted(lambda line: line.id)
        for line in self:
            move = self.env['stock.move'].search([('sale_line_id','=', line.id),('product_id', '=', line.product_id.id)]).filtered(lambda l: l.picking_id.state not in ['done', 'cancel']).sorted(lambda line: line.picking_id.id)
            if len(move) == 1: 
                line.do_reference = move.picking_id.name
            else:
                line.do_reference = ' '



    
    @api.depends('product_uom_qty', 'qty_delivered')
    def _compute_back_order_qty(self):
        for pro in self:
            pro.back_order_qty = pro.product_uom_qty - pro.qty_delivered

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id.name:
            self.update({'customer_part_no':self.product_id.name,
                         'name':self.product_id.x_studio_field_mHzKJ})

            
class AccountGeneralLedgerReport(models.AbstractModel):
    _inherit = "account.aged.partner.balance.report.handler"

    @api.model
    def _get_account_total_line(self, options, account, amount_currency, debit, credit, balance):
        return {
            'id': 'total_%s' % account.id,
            'class': 'o_account_reports_domain_total',
            'parent_id': 'account_%s' % account.id,
            'name': _('Total'),
            'columns': [
                {'name': '', 'class': 'number'},
                {'name': self.format_value(debit), 'class': 'number'},
                {'name': self.format_value(credit), 'class': 'number'},
                {'name': self.format_value(balance), 'class': 'number'},
            ],
            'colspan': 4,
        }

        
