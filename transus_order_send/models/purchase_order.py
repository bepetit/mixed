# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'transus.mixin']

    @api.multi
    def get_transus_order_date(self):
        self.ensure_one()
        return self.date_to_transus(self.date_order[:10])

    @api.multi
    def get_transus_delivery_date(self):
        self.ensure_one()
        return self.date_to_transus(self.date_planned[:10])

    def _check_transus_required_fields(self):
        self.ensure_one()
        #TODO complete
        res = super(PurchaseOrder, self)._check_transus_required_fields()
        if self._name == 'purchase.order':
            if not self.date_order:
                raise UserError('Order Date is required for Transus connector.')
            transus_gln = self.partner_id.transus_gln or self.partner_id.parent_id.transus_gln
            if not transus_gln:
                raise UserError('The GLN of the Partner is not set.')

        return res

    def _get_transus_template_order(self):
        return 'transus_order_send.order'

    def _prepare_transus_xml_message(self):
        res = super(PurchaseOrder, self)._prepare_transus_xml_message()
        if self._name == 'purchase.order':
            template = self._get_transus_template_order()
            xml = self.env['ir.ui.view'].render_template(
                template,
                values={
                    'self': self,
                },
            )
            return xml
        return res

    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for order in self:
            if order.partner_id.transus_supplier_sale_order_receiver or order.partner_id.parent_id.transus_supplier_sale_order_receiver:
                for line in order.order_line:
                    if not line.product_id:
                        raise UserError('Missing product in lines.')
                    elif not line.product_id.barcode:
                        raise UserError('Missing barcode in product.')
                order.to_transus()
        return res
