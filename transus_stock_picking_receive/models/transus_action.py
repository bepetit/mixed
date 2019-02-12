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
            if str(msg.MessageStandard) == 'TRANSUSXML' and str(msg.MessageType) == '6':
                if  self._check_picking(msg):
                    res = self._get_existing_picking(msg)
                    if res:
                        self._update_existing_picking(res, msg)
                    else:
                        res = self._create_picking(msg)
        return res

    def _check_picking(self, msg):
        partner_ok = self._transus_picking_check_partner(msg)
        if not partner_ok:
            return False
        company_ok = self._transus_picking_check_company_partner(msg)
        if not company_ok:
            return False
        company_ok = self._transus_picking_check_company(msg)
        if not company_ok:
            return False
        picking_type = self._transus_picking_check_type(msg)
        if not picking_type:
            return False
        order_number_buyer = self._transus_picking_check_order_number_buyer(msg)
        if not order_number_buyer:
            return False

        for line in msg.Article:
            line_product_ok = self._transus_picking_check_line_product(line)
            if not line_product_ok:
                return False

        return True

    def _get_existing_picking(self, msg):
        partner = self._transus_picking_get_partner(msg)
        company = self._transus_picking_get_company(msg)
        picking_type = self._transus_picking_get_type(company)
        order_number_buyer = str(msg.OrderNumberBuyer)

        existing_picking = self.env['stock.picking'].search([
            ('partner_id', '=', partner.id),
            ('company_id', '=', company.id),
            ('picking_type_id', '=', picking_type.id),
            ('state', '!=', 'done'),
            ('origin', '=', order_number_buyer),  # eg.: OrderNumberBuyer == field origin PO/MXD/0005342
        ], limit=1)
        return existing_picking

    def _update_existing_picking(self, picking, msg):
        message_body = _("Picking <em>%s</em> <b>received</b> with following lines:<br/>\n") % (picking.name)
        for line in msg.Article:
            message_body += '<ul>'
            product = self._transus_picking_get_line_product(line)
            message_body += '<li>' + product.name + ': ' + str(line.DeliveredQuantityUnits) + '</li>\n'
            message_body += '</ul>'
        picking.message_post(body=message_body)

    def _create_picking(self, msg):
        partner = self._transus_picking_get_partner(msg)
        company = self._transus_picking_get_company(msg)
        picking_type = self._transus_picking_get_type(company)
        order_number_buyer = str(msg.OrderNumberBuyer)
        location = self._transus_get_src_location(partner, picking_type)

        # TODO IsTestMessage
        vals = {
            'partner_id': partner.id,
            'company_id': company.id,
            # 'date': self.date_from_transus(msg.DespatchAdviceDate),
            # 'date_done': self.date_from_transus(msg.DespatchDate),
            'origin': order_number_buyer,
            'picking_type_id': picking_type.id,
            'location_id': location.id,
        }

        new_picking = self.env['stock.picking'].with_context(
            default_picking_type_id=picking_type.id
        ).create(vals)

        for line in msg.Article:
            product = self._transus_picking_get_line_product(line)
            vals = {
                'name': product.name,
                'partner_id': partner.id,
                'company_id': company.id,
                # 'date': self.date_from_transus(msg.DespatchDate),
                'product_id': product.id,
                'product_uom': product.uom_id.id,
                'product_uom_qty': line.DeliveredQuantityUnits,
                'picking_id': new_picking.id,
                'location_id': new_picking.location_id.id,
                'location_dest_id': new_picking.location_dest_id.id,
            }
            self.env['stock.move'].create(vals)
        return new_picking

    def _transus_picking_get_partner(self, msg):
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

    def _transus_picking_check_partner(self, msg):
        if not msg.SupplierGLN:
            self.error_message = 'No SupplierGLN found'
            self.error_on_parsing = True
            return False
        partner = self._transus_picking_get_partner(msg)
        if not partner:
            self.error_message = 'No Partner with GLN=%s found.' % str(msg.SupplierGLN)
            self.error_on_parsing = True
            return False
        if len(partner) > 1:
            self.error_message = 'More than one Partner with GLN=%s found.' % str(msg.SupplierGLN)
            self.error_on_parsing = True
            return False
        return True

    def _transus_picking_get_company_partner(self, msg):
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

    def _transus_picking_check_company_partner(self, msg):
        if not msg.BuyerGLN:
            self.error_message = 'No BuyerGLN found'
            self.error_on_parsing = True
            return False
        partner = self._transus_picking_get_company_partner(msg)
        if not partner:
            self.error_message = 'No Partner with GLN=%s found.' % str(msg.BuyerGLN)
            self.error_on_parsing = True
            return False
        if len(partner) > 1:
            self.error_message = 'More than one Partner with GLN=%s found.' % str(msg.BuyerGLN)
            self.error_on_parsing = True
            return False
        return True

    def _transus_picking_get_company(self, msg):
        partner = self._transus_picking_get_company_partner(msg)
        company = self.env['res.company'].search([
            ('partner_id', '=', partner.id)
        ])
        return company

    def _transus_picking_check_company(self, msg):
        company_gln = str(msg.BuyerGLN)
        company = self._transus_picking_get_company(msg)
        if not company:
            self.error_message = 'No Company with GLN=%s found.' % company_gln
            self.error_on_parsing = True
            return False
        if len(company) > 1:
            self.error_message = 'More than one Company with GLN=%s found.' % company_gln
            self.error_on_parsing = True
            return False
        return True

    def _transus_picking_get_type(self, company):
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id.company_id', '=', company.id),
        ], order='sequence', limit=1)
        return picking_type

    def _transus_picking_check_type(self, msg):
        company = self._transus_picking_get_company(msg)
        picking_type = self._transus_picking_get_type(company)
        if not picking_type:
            self.error_message = 'No picking_type with code=incoming found.'
            self.error_on_parsing = True
            return False
        # if len(picking_type) > 1:
        #     self.error_message = 'More than one picking_type with code=incoming found.'
        #     self.error_on_parsing = True
        #     return False
        return True

    def _transus_get_src_location(self, partner, picking_type):
        if picking_type.default_location_src_id:
            location = picking_type.default_location_src_id
        else:
            location = partner.property_stock_supplier
        return location

    def _transus_picking_get_line_product(self, line):
        product = self.env['product.product'].search([
            ('barcode', '=', line.GTIN)
        ])
        return product

    def _transus_picking_check_line_product(self, line):
        if not line.GTIN:
            self.error_message = 'No GTIN found'
            self.error_on_parsing = True
            return False
        product = self._transus_picking_get_line_product(line)
        if not product:
            self.error_message = 'No Product with GTIN=%s found.' % line.GTIN
            self.error_on_parsing = True
            return False
        if len(product) > 1:
            self.error_message = 'More than one Product with GTIN=%s found.' % line.GTIN
            self.error_on_parsing = True
            return False
        return True

    def _transus_picking_check_order_number_buyer(self, msg):
        if not msg.OrderNumberBuyer:
            self.error_message = 'No OrderNumberBuyer found'
            self.error_on_parsing = True
            return False
        return True
