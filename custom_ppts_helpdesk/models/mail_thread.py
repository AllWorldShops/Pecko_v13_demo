# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import datetime
import dateutil
import email
import hashlib
import hmac
import lxml
import logging
import pytz
import re
import socket
import time
import threading
try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib

from collections import namedtuple
from email.message import Message
from lxml import etree
from werkzeug import url_encode
from werkzeug import urls

from odoo import _, api, exceptions, fields, models, tools, registry, SUPERUSER_ID
from odoo.osv import expression

from odoo.tools import pycompat, ustr
from odoo.tools.misc import clean_context, split_every
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"
    
    @api.model
    def message_process(self, model, message, custom_values=None,
                        save_original=False, strip_attachments=False,
                        thread_id=None):
        """ Process an incoming RFC2822 email message, relying on
            ``mail.message.parse()`` for the parsing operation,
            and ``message_route()`` to figure out the target model.

            Once the target model is known, its ``message_new`` method
            is called with the new message (if the thread record did not exist)
            or its ``message_update`` method (if it did).

           :param string model: the fallback model to use if the message
               does not match any of the currently configured mail aliases
               (may be None if a matching alias is supposed to be present)
           :param message: source of the RFC2822 message
           :type message: string or xmlrpclib.Binary
           :type dict custom_values: optional dictionary of field values
                to pass to ``message_new`` if a new record needs to be created.
                Ignored if the thread record already exists, and also if a
                matching mail.alias was found (aliases define their own defaults)
           :param bool save_original: whether to keep a copy of the original
                email source attached to the message after it is imported.
           :param bool strip_attachments: whether to strip all attachments
                before processing the message, in order to save some space.
           :param int thread_id: optional ID of the record/thread from ``model``
               to which this mail should be attached. When provided, this
               overrides the automatic detection based on the message
               headers.
        """
        # extract message bytes - we are forced to pass the message as binary because
        # we don't know its encoding until we parse its headers and hence can't
        # convert it to utf-8 for transport between the mailgate script and here.
        if isinstance(message, xmlrpclib.Binary):
            message = bytes(message.data)
        if isinstance(message, str):
            message = message.encode('utf-8')
        message = email.message_from_bytes(message)

        # parse the message, verify we are not in a loop by checking message_id is not duplicated
        msg_dict = self.message_parse(message, save_original=save_original)
        if strip_attachments:
            msg_dict.pop('attachments', None)

        existing_msg_ids = self.env['mail.message'].search([('message_id', '=', msg_dict['message_id'])], limit=1)
        if existing_msg_ids:
            _logger.info('Ignored mail from %s to %s with Message-Id %s: found duplicated Message-Id during processing',
                         msg_dict.get('email_from'), msg_dict.get('to'), msg_dict.get('message_id'))
            return False

        # find possible routes for the message
        routes = self.message_route(message, msg_dict, model, thread_id, custom_values)
        try:
            print(routes)
            _logger.info(str(routes)+"Checking Incoming mail")
            if model or routes:
                if model == 'helpdesk.ticket' or routes[0][0] == 'helpdesk.ticket' and routes[0][1]:
                    _logger.info(str(model)+"Inside Model")
                    help_id = self.env['helpdesk.ticket'].sudo().browse(routes[0][1])
                    
                    if help_id:
                        _logger.info(str(help_id)+"inside help_id")
                        if help_id.stage_id.solved:
                            if help_id.team_id:
                                if help_id.team_id.stage_ids:
                                    _logger.info(str(help_id.team_id._determine_stage()[help_id.team_id.id])+"inside help_id")
                                    help_id.stage_id = help_id.team_id._determine_stage()[help_id.team_id.id]
#                             ori_routes=routes[0]
#                             list_routes=list(ori_routes)
#                             list_routes[1] = None
#                             routes[0] = tuple(list_routes)
        except Exception as e:
            print(e)
            print(routes)
            
        thread_id = self._message_route_process(message, msg_dict, routes)
        return thread_id
    
