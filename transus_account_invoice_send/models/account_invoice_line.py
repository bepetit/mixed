# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    def get_transus_invoice_line_vat_percentage(self):
        self.ensure_one()

        # TODO also check amount_type
        return self.invoice_line_tax_ids.amount
