from odoo import models, fields, api, _

class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_credit_journal = fields.Boolean(string="Is Credit?")
    is_debit_journal= fields.Boolean(string="Is Debit Note?")