# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'transus.mixin']

    @api.multi
    def get_transus_despatch_date(self):
        self.ensure_one()
        return self.date_to_transus(self.min_date[:10])

    # @api.multi
    # def get_transus_despatch_advice_date(self):
    #     self.ensure_one()
    #     return self.date_to_transus(self.date)

    @api.multi
    def get_transus_picking_type(self):
        self.ensure_one()
        # TODO?
        return 'incoming'

    def _check_transus_required_fields(self):
        self.ensure_one()
        #TODO complete
        res = super(StockPicking, self)._check_transus_required_fields()
        if self._name == 'stock.picking':
            if not self.partner_id:
                raise UserError('Partner is required for Transus connector.')
            if not self.date:
                raise UserError('Date is required for Transus connector.')
            # if not self.date_done:
            #     raise UserError('Delivery Date is required for Transus connector.')
            transus_gln = self.partner_id.transus_gln or self.partner_id.parent_id.transus_gln
            if not transus_gln:
                raise UserError('The GLN of the Partner is not set.')

        return res

    def _get_transus_template_picking(self):
        return 'transus_stock_picking_send.picking'

    def _prepare_transus_xml_message(self):
        res = super(StockPicking, self)._prepare_transus_xml_message()
        if self._name == 'stock.picking':
            template = self._get_transus_template_picking()
            xml = self.env['ir.ui.view'].render_template(
                template,
                values={
                    'self': self,
                },
            )
            return xml
        return res

    @api.multi
    def do_new_transfer(self):
        res = super(StockPicking, self).do_new_transfer()
        for picking in self:
            if picking.picking_type_id.code == 'outgoing':
                if picking.partner_id.transus_customer_picking_receiver:
                    picking.to_transus()
                elif picking.partner_id.parent_id.transus_customer_picking_receiver:
                    picking.to_transus()
        return res
