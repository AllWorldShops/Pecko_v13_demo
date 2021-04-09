# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.




from odoo import _, api, exceptions, fields, models, tools, registry, SUPERUSER_ID


class HelpdeskStage(models.Model):
    _inherit = "helpdesk.stage"
    
    solved = fields.Boolean("Solved ?")