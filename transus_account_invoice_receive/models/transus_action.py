# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class TransusAction(models.Model):
    _inherit = 'transus.action'

    @api.multi
    def _transus_create_object_received(self, res_message):
        res = super(TransusAction, self)._transus_create_object_received(res_message)
        if not res and res_message.tag == 'Messages':
            msg = res_message.Message
            if str(msg.MessageStandard) == 'TRANSUSXML' and str(msg.MessageType) == '8':
                if self._check_invoice(msg):
                    res = self._create_invoice(msg)
                    for line in msg.Article:
                        self._create_invoice_line(line, res)
        return res

    def _check_invoice(self, msg):
        partner_ok = self._transus_invoice_check_partner(msg)
        if not partner_ok:
            return False
        company_ok = self._transus_invoice_check_company_partner(msg)
        if not company_ok:
            return False
        company_ok = self._transus_invoice_check_company(msg)
        if not company_ok:
            return False
        currency_ok = self._transus_invoice_check_currency(msg)
        if not currency_ok:
            return False
        order_number_buyer = self._transus_invoice_check_order_number_buyer(msg)
        if not order_number_buyer:
            return False

        for line in msg.Article:
            line_vat_ok = self._transus_invoice_check_line_vat(line, msg)
            if not line_vat_ok:
                return False
            line_product_ok = self._transus_invoice_check_line_product(line)
            if not line_product_ok:
                return False
            # line_account_ok = self._transus_invoice_check_line_account(line)
            # if not line_account_ok:
            #     return False

        return True

    def _create_invoice(self, msg):

        inv_type = self._transus_invoice_get_type(msg)
        partner = self._transus_invoice_get_partner(msg)
        company = self._transus_invoice_get_company(msg)
        currency = self._transus_invoice_get_currency(msg)
        order_number_buyer = str(msg.OrderNumberBuyer)
        purchase = self.env['purchase.order'].search([
            ('name', '=', order_number_buyer),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        journal = self.env['account.invoice'].with_context(
            type='in_invoice'
        )._default_journal()

        # TODO IsTestMessage
        vals = {
            'type': inv_type,
            'partner_id': partner.id,
            'company_id': company.id,
            'date_invoice': self.date_from_transus(msg.InvoiceDate),
            'reference': msg.InvoiceNumber,
            'journal_id': journal.id,
            'reference_type': 'none',
            'currency_id': currency.id,
            'purchase_id': purchase.id,
        }

        new_invoice = self.env['account.invoice'].create(vals)
        return new_invoice

    def _create_invoice_line(self, line, new_invoice):
        vat = self._transus_invoice_get_line_vat(line, new_invoice.company_id)
        product = self._transus_invoice_get_line_product(line)
        account_id = self._transus_invoice_get_line_account(line, new_invoice)
        vals = {
            'name': product.name,
            'price_unit': line.ArticlePrice,
            'quantity': line.InvoicedQuantity,
            'product_id': product.id,
            'account_id': account_id,
            'invoice_id': new_invoice.id,
        }
        new_invoice_line = self.env['account.invoice.line'].create(vals)
        new_invoice_line.invoice_line_tax_ids |= vat

    def _transus_invoice_get_partner(self, msg):
        partner_gln = str(msg.SupplierGLN)
        partner = self.env['res.partner'].search([
            ('transus_gln', '=', partner_gln),
            ('company_id', '=', self.company_id.id)
        ])
        if not partner:
            partner = self.env['res.partner'].search([
                ('transus_gln', '=', partner_gln),
                ('company_id', '=', False)
            ])
        return partner

    def _transus_invoice_check_partner(self, msg):
        if not msg.SupplierGLN:
            self.error_message = 'No SupplierGLN found'
            self.error_on_parsing = True
            return False
        partner = self._transus_invoice_get_partner(msg)
        if not partner:
            self.error_message = 'No Partner with GLN=%s found.' % str(msg.SupplierGLN)
            self.error_on_parsing = True
            return False
        if len(partner) > 1:
            self.error_message = 'More than one Partner with GLN=%s found.' % str(msg.SupplierGLN)
            self.error_on_parsing = True
            return False
        return True

    def _transus_invoice_get_company_partner(self, msg):
        partner_gln = str(msg.BuyerGLN)
        partner = self.env['res.partner'].search([
            ('transus_gln', '=', partner_gln),
            ('company_id', '=', self.company_id.id)
        ])
        if not partner:
            partner = self.env['res.partner'].search([
                ('transus_gln', '=', partner_gln),
                ('company_id', '=', False)
            ])
        return partner

    def _transus_invoice_check_company_partner(self, msg):
        if not msg.BuyerGLN:
            self.error_message = 'No BuyerGLN found'
            self.error_on_parsing = True
            return False
        partner = self._transus_invoice_get_company_partner(msg)
        if not partner:
            self.error_message = 'No Partner with GLN=%s found.' % str(msg.BuyerGLN)
            self.error_on_parsing = True
            return False
        if len(partner) > 1:
            self.error_message = 'More than one Partner with GLN=%s found.' % str(msg.BuyerGLN)
            self.error_on_parsing = True
            return False
        return True

    def _transus_invoice_get_company(self, msg):
        partner = self._transus_invoice_get_company_partner(msg)
        company = self.env['res.company'].search([
            ('partner_id', '=', partner.id)
        ])
        return company

    def _transus_invoice_check_company(self, msg):
        company_gln = str(msg.BuyerGLN)
        company = self._transus_invoice_get_company(msg)
        if not company:
            self.error_message = 'No Company with GLN=%s found.' % company_gln
            self.error_on_parsing = True
            return False
        if len(company) > 1:
            self.error_message = 'More than one Company with GLN=%s found.' % company_gln
            self.error_on_parsing = True
            return False
        return True

    def _transus_invoice_get_currency(self, msg):
        currency_code = str(msg.CurrencyCode)
        currency = self.env['res.currency'].search([
            ('name', '=', currency_code)
        ])
        return currency

    def _transus_invoice_check_currency(self, msg):
        if not msg.CurrencyCode:
            self.error_message = 'No CurrencyCode found'
            self.error_on_parsing = True
            return False
        currency_code = str(msg.CurrencyCode)
        currency = self._transus_invoice_get_currency(msg)
        if not currency:
            self.error_message = 'No Currency with name=%s found.' % currency_code
            self.error_on_parsing = True
            return False
        if len(currency) > 1:
            self.error_message = 'More than one Currency with name=%s found.' % currency_code
            self.error_on_parsing = True
            return False
        return True

    def _transus_invoice_get_type(self, msg):
        inv_type = 'in_invoice'
        if msg.InvoiceType != 'NOR':
            inv_type = 'in_refund'
        return inv_type

    def _transus_invoice_get_line_vat(self, line, company):
        vats = self.env['account.tax'].search([
            ('amount', '=', line.ArticleVATPercentage),
            ('type_tax_use', '=', 'purchase'),
            ('company_id', '=', company.id),
        ])
        return vats

    def _transus_invoice_check_line_vat(self, line, msg):
        if not line.ArticleVATPercentage:
            self.error_message = 'No ArticleVATPercentage found'
            self.error_on_parsing = True
            return False
        company = self._transus_invoice_get_company(msg)
        vats = self._transus_invoice_get_line_vat(line, company)
        if not vats:
            self.error_message = 'No VAT with percentage=%s found.' % line.ArticleVATPercentage
            self.error_on_parsing = True
            return False
        if len(vats) > 1:
            self.error_message = 'More than one VAT with percentage=%s found.' % line.ArticleVATPercentage
            self.error_on_parsing = True
            return False
        return True

    def _transus_invoice_get_line_product(self, line):
        product = self.env['product.product'].search([
            ('barcode', '=', line.GTIN)
        ])
        return product

    def _transus_invoice_check_line_product(self, line):
        if not line.GTIN:
            self.error_message = 'No GTIN found'
            self.error_on_parsing = True
            return False
        product = self._transus_invoice_get_line_product(line)
        if not product:
            self.error_message = 'No Product with GTIN=%s found.' % line.GTIN
            self.error_on_parsing = True
            return False
        if len(product) > 1:
            self.error_message = 'More than one Product with GTIN=%s found.' % line.GTIN
            self.error_on_parsing = True
            return False
        return True

    def _transus_invoice_get_line_account(self, line, new_invoice):
        journal = new_invoice.journal_id
        account = self.env['account.invoice.line'].with_context(
            journal_id=journal.id,
            type='in_invoice'
        )._default_account()
        return account

    # def _transus_invoice_check_line_account(self, line, new_invoice):
    #     journal = new_invoice.journal_id
    #     account = self._transus_invoice_get_line_account(line, new_invoice)
    #     if not account:
    #         self.error_message = 'No Account available for journal=%s found.' % journal.id
    #         self.error_on_parsing = True
    #         return False
    #     return True

    def _transus_invoice_check_order_number_buyer(self, msg):
        if not msg.OrderNumberBuyer:
            self.error_message = 'No OrderNumberBuyer found'
            self.error_on_parsing = True
            return False
        return True
