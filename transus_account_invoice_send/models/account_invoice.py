# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'transus.mixin']

    @api.multi
    def get_transus_invoice_date(self):
        self.ensure_one()
        return self.date_to_transus(self.date_invoice)

    @api.multi
    def get_transus_invoice_type(self):
        self.ensure_one()
        # COR=Correctie, CRE=Credit factuur, NOR=Normaal
        # TODO: COR
        if self.type in ['out_refund', 'in_refund']:
            return 'CRE'
        return 'NOR'

    def _check_transus_required_fields(self):
        self.ensure_one()
        #TODO complete
        res = super(AccountInvoice, self)._check_transus_required_fields()
        if self._name == 'account.invoice':
            if not self.date_invoice:
                raise UserError('Invoice Date is required for Transus connector.')
            transus_gln = self.partner_id.transus_gln or self.partner_id.parent_id.transus_gln
            if not transus_gln:
                raise UserError('The GLN of the Partner is not set.')

            # Limit to one tax only
            for line in self.invoice_line_ids:
                if len(line.invoice_line_tax_ids) > 1:
                    raise UserError('Only one tax per invoice line is supported.')
        return res

    def _get_transus_template_invoice(self):
        return 'transus_account_invoice_send.invoice'

    def _prepare_transus_xml_message(self):
        res = super(AccountInvoice, self)._prepare_transus_xml_message()
        if self._name == 'account.invoice':
            template = self._get_transus_template_invoice()
            xml = self.env['ir.ui.view'].render_template(
                template,
                values={
                    'self': self,
                },
            )
            return xml
        return res

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        for invoice in self:
            if invoice.partner_id.transus_customer_invoice_receiver:
                invoice.to_transus()
            elif invoice.partner_id.parent_id.transus_customer_invoice_receiver:
                invoice.to_transus()
        return res
