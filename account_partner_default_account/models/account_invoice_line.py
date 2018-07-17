# -*- coding: utf-8 -*-
# Copyright 2017 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def _default_account(self):
        partner_id = self._context.get('partner_id')
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if self._context.get('type') in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'):
                if partner.partner_default_account:
                    return partner.partner_default_account
        return super(AccountInvoiceLine, self)._default_account()

    account_id = fields.Many2one(default=_default_account)
