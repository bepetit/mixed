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
        if not res and res_message.tag == 'ORDERS':
            if self._check_sale_order(res_message.ORDER):
                res = self._create_sale_order(res_message.ORDER)
        return res

    def _check_sale_order(self, msg):
        partner_ok = self._transus_sale_order_check_partner(msg.HEADER)
        if not partner_ok:
            return False
        company_ok = self._transus_sale_order_check_company_partner(msg.HEADER)
        if not company_ok:
            return False
        company_ok = self._transus_sale_order_check_company(msg.HEADER)
        if not company_ok:
            return False
        currency_ok = self._transus_sale_order_check_currency(msg.HEADER)
        if not currency_ok:
            return False
        for line in msg.ARTICLE:
            line_product_ok = self._transus_sale_order_check_line_product(line)
            if not line_product_ok:
                return False

        return True

    def _create_sale_order(self, msg):
        partner = self._transus_sale_order_get_partner(msg.HEADER)
        company = self._transus_sale_order_get_company(msg.HEADER)
        currency = self._transus_sale_order_get_currency(msg.HEADER)
        client_order_ref = msg.HEADER.OrderNumberBuyer

        # TODO IsTestMessage ?
        vals = {
            'partner_id': partner.id,
            'company_id': company.id,
            'client_order_ref': client_order_ref,
            'currency_id': currency.id,
            'commitment_date': self.date_from_transus(msg.HEADER.RequestedDeliveryDate),
            'confirmation_date': self.date_from_transus(msg.HEADER.OrderDate),
        }

        new_sale_order = self.env['sale.order'].create(vals)
        new_sale_order.onchange_partner_id()

        for line in msg.ARTICLE:
            product = self._transus_sale_order_get_line_product(line)
            vals = {
                'product_uom_qty': line.OrderedQuantity,
                'product_id': product.id,
                'order_id': new_sale_order.id,
            }
            vals.update(self.env['sale.order.line']._prepare_add_missing_fields(vals))
            self.env['sale.order.line'].create(vals)
        return new_sale_order

    def _transus_sale_order_get_partner(self, msg):
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

    def _transus_sale_order_check_partner(self, msg):
        if not msg.BuyerGLN:
            self.error_message = 'No BuyerGLN found'
            self.error_on_parsing = True
            return False
        partner = self._transus_sale_order_get_partner(msg)
        if not partner:
            self.error_message = 'No Partner with GLN=%s found.' % str(msg.BuyerGLN)
            self.error_on_parsing = True
            return False
        if len(partner) > 1:
            self.error_message = 'More than one Partner with GLN=%s found.' % str(msg.BuyerGLN)
            self.error_on_parsing = True
            return False
        return True

    def _transus_sale_order_get_company_partner(self, msg):
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

    def _transus_sale_order_check_company_partner(self, msg):
        if not msg.SupplierGLN:
            self.error_message = 'No SupplierGLN found'
            self.error_on_parsing = True
            return False
        partner = self._transus_sale_order_get_company_partner(msg)
        if not partner:
            self.error_message = 'No Partner with GLN=%s found.' % str(msg.SupplierGLN)
            self.error_on_parsing = True
            return False
        if len(partner) > 1:
            self.error_message = 'More than one Partner with GLN=%s found.' % str(msg.SupplierGLN)
            self.error_on_parsing = True
            return False
        return True

    def _transus_sale_order_get_company(self, msg):
        partner = self._transus_sale_order_get_company_partner(msg)
        company = self.env['res.company'].search([
            ('partner_id', '=', partner.id)
        ])
        return company

    def _transus_sale_order_check_company(self, msg):
        company_gln = str(msg.SupplierGLN)
        company = self._transus_sale_order_get_company(msg)
        if not company:
            self.error_message = 'No Company with GLN=%s found.' % company_gln
            self.error_on_parsing = True
            return False
        if len(company) > 1:
            self.error_message = 'More than one Company with GLN=%s found.' % company_gln
            self.error_on_parsing = True
            return False
        return True

    def _transus_sale_order_get_currency(self, msg):
        currency_code = str(msg.CurrencyCode)
        currency = self.env['res.currency'].search([
            ('name', '=', currency_code)
        ])
        return currency

    def _transus_sale_order_check_currency(self, msg):
        if not msg.CurrencyCode:
            self.error_message = 'No CurrencyCode found'
            self.error_on_parsing = True
            return False
        currency_code = str(msg.CurrencyCode)
        currency = self._transus_sale_order_get_currency(msg)
        if not currency:
            self.error_message = 'No Currency with name=%s found.' % currency_code
            self.error_on_parsing = True
            return False
        if len(currency) > 1:
            self.error_message = 'More than one Currency with name=%s found.' % currency_code
            self.error_on_parsing = True
            return False
        return True

    def _transus_sale_order_get_line_product(self, line):
        product = self.env['product.product'].search([
            ('barcode', '=', line.GTIN)
        ])
        return product

    def _transus_sale_order_check_line_product(self, line):
        if not line.GTIN:
            self.error_message = 'No GTIN found'
            self.error_on_parsing = True
            return False
        product = self._transus_sale_order_get_line_product(line)
        if not product:
            self.error_message = 'No Product with GTIN=%s found.' % line.GTIN
            self.error_on_parsing = True
            return False
        if len(product) > 1:
            self.error_message = 'More than one Product with GTIN=%s found.' % line.GTIN
            self.error_on_parsing = True
            return False
        return True
