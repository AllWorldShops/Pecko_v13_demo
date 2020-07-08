# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime,date

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    message_last_post = fields.Datetime('')
    x_studio_field_CY3Z4 = fields.Char(string='Customer Part Number')
    x_studio_field_IMTtD = fields.Char(string='Description')
    x_studio_field_E1iTU = fields.Selection([('Please Select', 'Please Select'),('Confirmed', 'Confirmed'),('Not Confirmed','Not Confirmed')],string='Verification Status')

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    x_studio_field_c9hp1 = fields.Char(string='Position')
    x_studio_field_R7iUY = fields.Date(string='Effective Date')
    x_studio_field_bzUKS = fields.Date(string='Expiry Date')
    x_studio_field_SDGOp = fields.Char(string=' ')
    x_studio_field_8LNnO = fields.Char(string=' ')
    x_studio_field_gVfQK = fields.Char(string='Description')


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    baan4_task_code = fields.Char('Baan4 Task Code')

class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    x_studio_field_0zbIN = fields.Selection([('PECKO CN - Raw Materials', 'PECKO CN - Raw Materials'),('PECKO CN - Production', 'PECKO CN - Production'),('PECKO CN - Finished Goods','PECKO CN - Finished Goods')],string='Kanban Seq.')

class MrpRouting(models.Model):
    _inherit = 'mrp.routing'
    
    x_code = fields.Char(string='Code')

class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'
    
    x_code = fields.Char(string='Code')