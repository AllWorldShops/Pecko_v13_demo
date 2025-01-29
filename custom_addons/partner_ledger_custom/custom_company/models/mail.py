
import datetime
import logging
import threading
import re

from collections import defaultdict

from odoo import _, api, fields, models
from odoo import tools
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    # ============================================================
    # Changed batch_size:15000 as per the previous customization.
    # ============================================================
    @api.model
    def process_email_queue(self, ids=None, batch_size=15000):
        """Send immediately queued messages, committing after each
           message is sent - this is not transactional and should
           not be called during another transaction!

        A maximum of 1K MailMail (configurable using 'mail.mail.queue.batch.size'
        optional ICP) are fetched in order to keep time under control.

        :param list ids: optional list of emails ids to send. If given only
                         scheduled and outgoing emails within this ids list
                         are sent;
        :param dict context: if a 'filters' key is present in context,
                             this value will be used as an additional
                             filter to further restrict the outgoing
                             messages to send (by default all 'outgoing'
                             'scheduled' messages are sent).
        """
        domain = [
            '&',
            ('state', '=', 'outgoing'),
            '|',
            ('scheduled_date', '=', False),
            ('scheduled_date', '<=', datetime.datetime.utcnow()),
        ]
        if 'filters' in self._context:
            domain.extend(self._context['filters'])
        batch_size = int(self.env['ir.config_parameter'].sudo().get_param('mail.mail.queue.batch.size', batch_size))
        send_ids = self.search(domain, limit=batch_size if not ids else batch_size * 10).ids
        if not ids:
            ids_done = set()
            total = len(send_ids) if len(send_ids) < batch_size else self.search_count(domain)

            def post_send_callback(ids):
                """ Track mail ids that have been sent, and notify cron progress accordingly. """
                ids_done.update(send_ids)
                self.env['ir.cron']._notify_progress(done=len(ids_done), remaining=total - len(ids_done))
        else:
            send_ids = list(set(send_ids) & set(ids))
            post_send_callback = None

        send_ids.sort()

        res = None
        try:
            # auto-commit except in testing mode
            auto_commit = not getattr(threading.current_thread(), 'testing', False)
            res = self.browse(send_ids).send(auto_commit=auto_commit, post_send_callback=post_send_callback)
        except Exception:
            _logger.exception("Failed processing mail queue")

        return res