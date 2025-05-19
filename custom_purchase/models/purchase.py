# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo import tools
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.tools.safe_eval import safe_eval
import base64
from collections import defaultdict
import datetime
from odoo.tools import groupby
from odoo.tools import float_compare, float_is_zero
import logging
from odoo.tools import float_compare, float_is_zero
from dateutil.relativedelta import relativedelta
import psycopg2
import smtplib
from dateutil.relativedelta import relativedelta
import threading
import re
from odoo.addons.stock.models.stock_rule import ProcurementException


_logger = logging.getLogger(__name__)



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    old_po_no = fields.Char(string='Old PO Number')

    @api.model_create_multi
    def create(self, vals_list):
        orders = self.browse()
        partner_vals_list = []
        for vals in vals_list:
            company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
            # Ensures default picking type and currency are taken from the right company.
            self_comp = self.with_company(company_id)
            if vals.get('name', 'New') == 'New':
                seq_date = fields.datetime.now()

                # if 'date_order' in vals:
                #     seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
                vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase.order', sequence_date=seq_date) or '/'
            vals, partner_vals = self._write_partner_values(vals)
            partner_vals_list.append(partner_vals)
            orders |= super(PurchaseOrder, self_comp).create(vals)
        for order, partner_vals in zip(orders, partner_vals_list):
            if partner_vals:
                order.sudo().write(partner_vals)  # Because the purchase user doesn't have write on `res.partner`
        return orders

    # passing the values customer_po_no field , purchase order to sale order)
    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        val = super(PurchaseOrder, self)._prepare_sale_order_data(name, partner, company, direct_delivery_address)
        val['customer_po_no'] = self.name
        return val

    # passing the values line_no field , purchase order to sale order)
    @api.model
    def _prepare_sale_order_line_data(self, line, company, sale_id):
        res = super(PurchaseOrder, self)._prepare_sale_order_line_data(line, company, sale_id)
        res['line_no'] = line.line_no
        res['customer_part_no'] = line.customer_part_no
        res['requested_date_line'] = line.date_planned
        return res

    def inter_company_create_sale_order(self, company):
        """ Create a Sales Order from the current PO (self)
            Note : In this method, reading the current PO is done as sudo, and the creation of the derived
            SO as intercompany_user, minimizing the access right required for the trigger user.
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        self = self.with_context(force_company=company.id)
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']
        # find user for creating and validation SO/PO from partner company
        intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
        if not intercompany_uid:
            raise Warning(_('Provide at least one user for inter company relation for % ') % company.name)
        # check intercompany user access rights
        if not SaleOrder.with_user(intercompany_uid).check_access_rights('create', raise_exception=False):
            raise Warning(_("Inter company user of company %s doesn't have enough access rights") % company.name)

        for rec in self:
            # check pricelist currency should be same with SO/PO document
            company_partner = rec.company_id.partner_id.with_user(intercompany_uid)
            if rec.currency_id.id != company_partner.property_product_pricelist.currency_id.id:
                raise Warning(
                    _('You cannot create SO from PO because sale price list currency is different than purchase price list currency.')
                    + '\n'
                    + _('The currency of the SO is obtained from the pricelist of the company partner.')
                    + '\n\n ({} {}, {} {}, {} {} (ID: {}))'.format(
                        _('SO currency:'), company_partner.property_product_pricelist.currency_id.name,
                        _('Pricelist:'), company_partner.property_product_pricelist.display_name,
                        _('Partner:'), company_partner.display_name, company_partner.id,
                    )
                )

            # create the SO and generate its lines from the PO lines
            # read it as sudo, because inter-compagny user can not have the access right on PO
            so_no_list = []

            if company.split_so:

                for line in rec.order_line:
                    # stop

                    sale_order_data = rec.sudo()._prepare_sale_order_data(
                        rec.name, company_partner, company,
                        rec.dest_address_id and rec.dest_address_id.id or False)
                    inter_user = self.env['res.users'].sudo().browse(intercompany_uid)
                    sale_order = SaleOrder.with_context(allowed_company_ids=inter_user.company_ids.ids).with_user(intercompany_uid).create(sale_order_data)
                    so_no_list.append(sale_order.name)

                    so_line_vals = rec._prepare_sale_order_line_data(line, company, sale_order.id)
                    SaleOrderLine.with_user(intercompany_uid).with_context(
                        allowed_company_ids=inter_user.company_ids.ids).create(so_line_vals)
                    # lines are browse as sudo to access all data required to be copied on SO line (mainly for company dependent field like taxes)
                    # for line in rec.order_line.sudo():
                    #     so_line_vals = rec._prepare_sale_order_line_data(line, company, sale_order.id)
                    #     # TODO: create can be done in batch; this may be a performance bottleneck
                    #     SaleOrderLine.with_user(intercompany_uid).with_context(allowed_company_ids=inter_user.company_ids.ids).create(so_line_vals)
                # write vendor reference field on
                if not rec.partner_ref:
                    rec.partner_ref = ', '.join(so_no_list)
                #Validation of sales order
                if company.auto_validation:
                       sale_order.with_user(intercompany_uid).action_confirm()

            else:

                for rec in self:
                    # check pricelist currency should be same with SO/PO document
                    company_partner = rec.company_id.partner_id.with_user(intercompany_uid)
                    if rec.currency_id.id != company_partner.property_product_pricelist.currency_id.id:
                        raise Warning(
                            _('You cannot create SO from PO because sale price list currency is different than purchase price list currency.')
                            + '\n'
                            + _('The currency of the SO is obtained from the pricelist of the company partner.')
                            + '\n\n ({} {}, {} {}, {} {} (ID: {}))'.format(
                                _('SO currency:'), company_partner.property_product_pricelist.currency_id.name,
                                _('Pricelist:'), company_partner.property_product_pricelist.display_name,
                                _('Partner:'), company_partner.display_name, company_partner.id,
                            )
                        )

                    # create the SO and generate its lines from the PO lines
                    # read it as sudo, because inter-compagny user can not have the access right on PO
                    sale_order_data = rec.sudo()._prepare_sale_order_data(
                        rec.name, company_partner, company,
                        rec.dest_address_id and rec.dest_address_id.id or False)
                    inter_user = self.env['res.users'].sudo().browse(intercompany_uid)
                    sale_order = SaleOrder.with_context(allowed_company_ids=inter_user.company_ids.ids).with_user(
                        intercompany_uid).create(sale_order_data)
                    # lines are browse as sudo to access all data required to be copied on SO line (mainly for company dependent field like taxes)
                    for line in rec.order_line.sudo():
                        so_line_vals = rec._prepare_sale_order_line_data(line, company, sale_order.id)
                        # TODO: create can be done in batch; this may be a performance bottleneck
                        SaleOrderLine.with_user(intercompany_uid).with_context(
                            allowed_company_ids=inter_user.company_ids.ids).create(so_line_vals)

                    # write vendor reference field on PO
                    if not rec.partner_ref:
                        rec.partner_ref = sale_order.name
                    #Validation of sales order
                    if company.auto_validation:
                       sale_order.with_user(intercompany_uid).action_confirm()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer')
    notes = fields.Char(string='Notes')
    order_ref = fields.Char('Order Reference',related='order_id.name', store=True)
    vendor_id = fields.Many2one('res.partner',related='order_id.partner_id')
    schedule_date = fields.Datetime(related='order_id.date_planned')
    promise_date = fields.Datetime(string="Promised Date")
    order_date = fields.Datetime(related='order_id.date_order')
    back_order_qty = fields.Float(string='Pending Qty', compute='_compute_back_order_qty', store=True)
    line_no = fields.Integer(string='Position', default=False)
    old_po_no = fields.Char(string="Old PO Number", related="order_id.old_po_no")

    @api.model
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, supplier, po):
        partner = supplier.partner_id
        uom_po_qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id, rounding_method='HALF-UP')
        # _select_seller is used if the supplier have different price depending
        # the quantities ordered.
        seller = product_id.with_company(company_id)._select_seller(
            partner_id=partner,
            quantity=uom_po_qty,
            date=po.date_order and po.date_order.date(),
            uom_id=product_id.uom_po_id)
        product_taxes = product_id.supplier_taxes_id.filtered(lambda x: x.company_id.id == company_id.id)
        taxes = po.fiscal_position_id.map_tax(product_taxes)

        # price_unit = self.env['account.tax']._fix_tax_included_price_company(
        #     seller.price, product_taxes, taxes, company_id) if seller.price else 0.0

        # Working unit price change for base code and change the variable seller replace supplier(21/07/23)
        price_unit = self.env['account.tax']._fix_tax_included_price_company(
            supplier.price, product_taxes, taxes, company_id) if supplier.price > 0 else 0.0

        if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, po.currency_id, po.company_id, po.date_order or fields.Date.today())

        product_lang = product_id.with_prefetch().with_context(
            lang=partner.lang,
            partner_id=partner.id,
        )
        name = product_lang.with_context(seller_id=seller.id).display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        date_planned = self.order_id.date_planned or self._get_date_planned(seller, po=po)

        return {
            'name': name,
            'product_qty': uom_po_qty,
            'product_id': product_id.id,
            'product_uom': product_id.uom_po_id.id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'taxes_id': [(6, 0, taxes.ids)],
            'order_id': po.id,
        }

    @api.depends('product_qty', 'qty_received')
    def _compute_back_order_qty(self):
        for pro in self:
            # if pro.qty_received:
            pro.back_order_qty = pro.product_qty - pro.qty_received
            # else:
            #     pro.back_order_qty = 0

    @api.onchange('product_id')
    def onchange_purchase_line_product(self):
        if self.product_id:
            self.manufacturer_id = self.product_id.manufacturer_id

    @api.model
    def create(self, vals):
        if vals['product_id']:
            product_id = self.env['product.product'].search([('id','=',vals['product_id'])])
            vals['manufacturer_id'] = product_id.product_tmpl_id.manufacturer_id.id
        return super(PurchaseOrderLine, self).create(vals)

#
class PurchaseOrdLine(models.Model):
    _inherit = 'purchase.order.line'

    item_text = fields.Char("Item Text", related='product_id.item_text')


class ResCompany(models.Model):
    _inherit = 'res.company'

    split_so = fields.Boolean(string="Split Sale Order")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    split_so = fields.Boolean(related='company_id.split_so', readonly=False)

class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None, alias_domain_id=False,
              mail_server=False, post_send_callback=None):
        IrMailServer = self.env['ir.mail_server']
        IrAttachment = self.env['ir.attachment']
        for mail_id in self.ids:
            success_pids = []
            failure_type = None
            processing_pid = None
            mail = None
            try:
                mail = self.browse(mail_id)

                # Skip if not outgoing
                if mail.state != 'outgoing':
                    if mail.state != 'exception' and mail.auto_delete:
                        mail.sudo().unlink()
                    continue

                # remove attachments if user send the link with the access_token
                body = mail.body_html or ''
                attachments = mail.attachment_ids
                for link in re.findall(r'/web/(?:content|image)/([0-9]+)', body):
                    attachments = attachments - IrAttachment.browse(int(link))

                # load attachment binary data with a separate read(), as prefetching all
                # `datas` (binary field) could bloat the browse cache, triggerring
                # soft/hard mem limits with temporary data.
                attachments = [(a['name'], base64.b64decode(a['datas']), a['mimetype'])
                               for a in attachments.sudo().read(['name', 'datas', 'mimetype']) if a['datas'] is not False]

                # specific behavior to customize the send email for notified partners
                email_list = []
                if mail.email_to:
                    email_list.append(mail._send_prepare_values())
                for partner in mail.recipient_ids:
                    values = mail._send_prepare_values(partner=partner)
                    values['partner_id'] = partner
                    email_list.append(values)

                # headers
                headers = {}
                ICP = self.env['ir.config_parameter'].sudo()
                bounce_alias = ICP.get_param("mail.bounce.alias")
                bounce_alias_static = tools.str2bool(ICP.get_param("mail.bounce.alias.static", "False"))
                catchall_domain = ICP.get_param("mail.catchall.domain")
                if bounce_alias and catchall_domain:
                    if bounce_alias_static:
                        headers['Return-Path'] = '%s@%s' % (bounce_alias, catchall_domain)
                    elif mail.mail_message_id.is_thread_message():
                        headers['Return-Path'] = '%s+%d-%s-%d@%s' % (
                        bounce_alias, mail.id, mail.model, mail.res_id, catchall_domain)
                    else:
                        headers['Return-Path'] = '%s+%d@%s' % (bounce_alias, mail.id, catchall_domain)
                if mail.headers:
                    try:
                        headers.update(safe_eval(mail.headers))
                    except Exception:
                        pass

                # Writing on the mail object may fail (e.g. lock on user) which
                # would trigger a rollback after actually sending the email.
                # To avoid sending twice the same email, provoke the failure earlier
                mail.write({
                    'state': 'exception',
                    'failure_reason': _(
                        'Error without exception. Probably due do sending an email without computed recipients.'),
                })
                # Update notification in a transient exception state to avoid concurrent
                # update in case an email bounces while sending all emails related to current
                # mail record.
                notifs = self.env['mail.notification'].search([
                    ('notification_type', '=', 'email'),
                    ('mail_mail_id', 'in', mail.ids),
                    ('notification_status', 'not in', ('sent', 'canceled'))
                ])
                if notifs:
                    notif_msg = _(
                        'Error without exception. Probably due do concurrent access update of notification records. Please see with an administrator.')
                    notifs.sudo().write({
                        'notification_status': 'exception',
                        'failure_type': 'unknown',
                        'failure_reason': notif_msg,
                    })
                    # `test_mail_bounce_during_send`, force immediate update to obtain the lock.
                    # see rev. 56596e5240ef920df14d99087451ce6f06ac6d36
                    # notifs.flush(fnames=['notification_status', 'failure_type', 'failure_reason'], records=notifs)
                    notifs.flush_recordset(['notification_status', 'failure_type', 'failure_reason'])

                # build an RFC2822 email.message.Message object and send it without queuing
                res = None
                # To show the other recipients name while receiving the mail
                email = []
                email_to = ""

                for partner in self.partner_ids:
                    email_to = email_to + partner.email + ","

                email_to = email_to.rstrip(",")

                for email in email_list:
                    msg = IrMailServer.build_email(
                        email_from=mail.email_from,
                        email_to=tools.email_split(email_to),
                        # email_to=email.get('email_to'),
                        subject=mail.subject,
                        body=email.get('body'),
                        body_alternative=email.get('body_alternative'),
                        email_cc=tools.email_split(mail.email_cc),
                        reply_to=mail.reply_to,
                        attachments=attachments,
                        message_id=mail.message_id,
                        references=mail.references,
                        object_id=mail.res_id and ('%s-%s' % (mail.res_id, mail.model)),
                        subtype='html',
                        subtype_alternative='plain',
                        headers=headers)
                    processing_pid = email.pop("partner_id", None)
                    try:
                        res = IrMailServer.send_email(
                            msg, mail_server_id=mail.mail_server_id.id, smtp_session=smtp_session)
                        if processing_pid:
                            success_pids.append(processing_pid)
                        processing_pid = None
                    except AssertionError as error:
                        if str(error) == IrMailServer.NO_VALID_RECIPIENT:
                            # if we have a list of void emails for email_list -> email missing, otherwise generic email failure
                            if not email.get('email_to') and failure_type != "mail_email_invalid":
                                failure_type = "mail_email_missing"
                            else:
                                failure_type = "mail_email_invalid"
                            # No valid recipient found for this particular
                            # mail item -> ignore error to avoid blocking
                            # delivery to next recipients, if any. If this is
                            # the only recipient, the mail will show as failed.
                            _logger.info("Ignoring invalid recipients for mail.mail %s: %s",
                                         mail.message_id, email.get('email_to'))
                        else:
                            raise

                        # if str(error) == IrMailServer.NO_VALID_RECIPIENT:
                        #     failure_type = "RECIPIENT"
                        #     # No valid recipient found for this particular
                        #     # mail item -> ignore error to avoid blocking
                        #     # delivery to next recipients, if any. If this is
                        #     # the only recipient, the mail will show as failed.
                        #     _logger.info("Ignoring invalid recipients for mail.mail %s: %s",
                        #                  mail.message_id, email.get('email_to'))
                        # else:
                        #     raise
                if res:  # mail has been sent at least once, no major exception occured
                    mail.write({'state': 'sent', 'message_id': res, 'failure_reason': False})
                    _logger.info('Mail with ID %r and Message-Id %r successfully sent', mail.id, mail.message_id)
                    # /!\ can't use mail.state here, as mail.refresh() will cause an error
                    # see revid:odo@openerp.com-20120622152536-42b2s28lvdv3odyr in 6.1
                mail._postprocess_sent_message(success_pids=success_pids, failure_type=failure_type)
            except MemoryError:
                # prevent catching transient MemoryErrors, bubble up to notify user or abort cron job
                # instead of marking the mail as failed
                _logger.exception(
                    'MemoryError while processing mail with ID %r and Msg-Id %r. Consider raising the --limit-memory-hard startup option',
                    mail.id, mail.message_id)
                # mail status will stay on ongoing since transaction will be rollback
                raise
            except (psycopg2.Error, smtplib.SMTPServerDisconnected):
                # If an error with the database or SMTP session occurs, chances are that the cursor
                # or SMTP session are unusable, causing further errors when trying to save the state.
                _logger.exception(
                    'Exception while processing mail with ID %r and Msg-Id %r.',
                    mail.id, mail.message_id)
                raise
            except Exception as e:
                failure_reason = tools.ustr(e)
                _logger.exception('failed sending mail (id: %s) due to %s', mail.id, failure_reason)
                mail.write({'state': 'exception', 'failure_reason': failure_reason})
                mail._postprocess_sent_message(success_pids=success_pids, failure_reason=failure_reason,
                                               failure_type='unknown')
                if raise_exception:
                    if isinstance(e, (AssertionError, UnicodeEncodeError)):
                        if isinstance(e, UnicodeEncodeError):
                            value = "Invalid text: %s" % e.object
                        else:
                            # get the args of the original error, wrap into a value and throw a MailDeliveryException
                            # that is an except_orm, with name and value as arguments
                            value = '. '.join(e.args)
                        raise MailDeliveryException(_("Mail Delivery Failed"), value)
                    raise

        if auto_commit is True:
            self._cr.commit()
        return True

#
# # commended by changes by ppts : for to create separate rfq based on reordering rules
# class StockRule(models.Model):
#     _inherit = "stock.rule"
#
#     @api.model
#     def _run_buy(self, procurements):
#
#         procurements_by_po_domain = defaultdict(list)
#         errors = []
#         for procurement, rule in procurements:
#
#             # Get the schedule date in order to find a valid seller
#             procurement_date_planned = fields.Datetime.from_string(procurement.values['date_planned'])
#
#             supplier = False
#             if procurement.values.get('supplierinfo_id'):
#                 supplier = procurement.values['supplierinfo_id']
#             elif procurement.values.get('orderpoint_id') and procurement.values['orderpoint_id'].supplier_id:
#                 supplier = procurement.values['orderpoint_id'].supplier_id
#             else:
#                 supplier = procurement.product_id.with_company(procurement.company_id.id)._select_seller(
#                     partner_id=procurement.values.get("supplierinfo_name"),
#                     quantity=procurement.product_qty,
#                     date=procurement_date_planned.date(),
#                     uom_id=procurement.product_uom)
#
#             # Fall back on a supplier for which no price may be defined. Not ideal, but better than
#             # blocking the user.
#             supplier = supplier or procurement.product_id._prepare_sellers(False).filtered(
#                 lambda s: not s.company_id or s.company_id == procurement.company_id
#             )[:1]
#
#             if not supplier:
#                 msg = _('There is no matching vendor price to generate the purchase order for product %s (no vendor defined, minimum quantity not reached, dates not valid, ...). Go on the product form and complete the list of vendors.') % (procurement.product_id.display_name)
#                 errors.append((procurement, msg))
#
#             partner = supplier.partner_id
#             # we put `supplier_info` in values for extensibility purposes
#             procurement.values['supplier'] = supplier
#             procurement.values['propagate_cancel'] = rule.propagate_cancel
#
#             domain = rule._make_po_get_domain(procurement.company_id, procurement.values, partner)
#             procurements_by_po_domain[domain].append((procurement, rule))
#
#         if errors:
#             raise ProcurementException(errors)
#
#         for domain, procurements_rules in procurements_by_po_domain.items():
#             # Get the procurements for the current domain.
#             # Get the rules for the current domain. Their only use is to create
#             # the PO if it does not exist.
#             procurements, rules = zip(*procurements_rules)
#
#             # Get the set of procurement origin for the current domain.
#             origins = set([p.origin for p in procurements])
#             # Check if a PO exists for the current domain.
#             print('domain',domain)
#             po = self.env['purchase.order'].sudo().search([dom for dom in domain], limit=1)
#             print('po',po)
#             company_id = procurements[0].company_id
#
#             # PPTS comment the below code for PO split concept requested by Suresh on 08.05.2023
#             # if not po or po:
#             if not po or po:
#                 positive_values = [p.values for p in procurements if float_compare(p.product_qty, 0.0, precision_rounding=p.product_uom.rounding) >= 0]
#                 if positive_values:
#                     # We need a rule to generate the PO. However the rule generated
#                     # the same domain for PO and the _prepare_purchase_order method
#                     # should only uses the common rules's fields.
#                     vals = rules[0]._prepare_purchase_order(company_id, origins, positive_values)
#                     # The company_id is the same for all procurements since
#                     # _make_po_get_domain add the company in the domain.
#                     # We use SUPERUSER_ID since we don't want the current user to be follower of the PO.
#                     # Indeed, the current user may be a user without access to Purchase, or even be a portal user.
#                     po = self.env['purchase.order'].with_company(company_id).with_user(SUPERUSER_ID).create(vals)
#             else:
#                 # If a purchase order is found, adapt its `origin` field.
#                 if po.origin:
#                     missing_origins = origins - set(po.origin.split(', '))
#                     if missing_origins:
#                         po.write({'origin': po.origin + ', ' + ', '.join(missing_origins)})
#                 else:
#                     po.write({'origin': ', '.join(origins)})
#
#             procurements_to_merge = self._get_procurements_to_merge(procurements)
#             procurements = self._merge_procurements(procurements_to_merge)
#
#             po_lines_by_product = {}
#             grouped_po_lines = groupby(po.order_line.filtered(lambda l: not l.display_type and l.product_uom == l.product_id.uom_po_id), key=lambda l: l.product_id.id)
#             for product, po_lines in grouped_po_lines:
#                 po_lines_by_product[product] = self.env['purchase.order.line'].concat(*po_lines)
#             po_line_values = []
#             for procurement in procurements:
#                 po_lines = po_lines_by_product.get(procurement.product_id.id, self.env['purchase.order.line'])
#                 po_line = po_lines._find_candidate(*procurement)
#
#                 if po_line:
#                     # If the procurement can be merge in an existing line. Directly
#                     # write the new values on it.
#                     vals = self._update_purchase_order_line(procurement.product_id,
#                         procurement.product_qty, procurement.product_uom, company_id,
#                         procurement.values, po_line)
#                     po_line.sudo().write(vals)
#                 else:
#                     if float_compare(procurement.product_qty, 0, precision_rounding=procurement.product_uom.rounding) <= 0:
#                         # If procurement contains negative quantity, don't create a new line that would contain negative qty
#                         continue
#                     # If it does not exist a PO line for current procurement.
#                     # Generate the create values for it and add it to a list in
#                     # order to create it in batch.
#                     partner = procurement.values['supplier'].partner_id
#                     location_dest_id= None,
#                     po_line_values.append(self.env['purchase.order.line']._prepare_purchase_order_line_from_procurement(
#                         procurement.product_id, procurement.product_qty,
#                          procurement.product_uom,
#                         location_dest_id,
#                         procurement.name,
#                         procurement.origin,
#                          procurement.company_id,
#                         procurement.values, po))
#                     # Check if we need to advance the order date for the new line
#                     order_date_planned = procurement.values['date_planned'] - relativedelta(
#                         days=procurement.values['supplier'].delay)
#                     if fields.Date.to_date(order_date_planned) < fields.Date.to_date(po.date_order):
#                         po.date_order = order_date_planned
#                     if fields.Date.to_date(order_date_planned) <= fields.Date.to_date(fields.Datetime.now()):
#                         po.date_order = fields.Datetime.now()
#             self.env['purchase.order.line'].sudo().create(po_line_values)
