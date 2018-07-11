# -*- coding: utf-8 -*-
# Copyright 2017 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields, _


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def get_shipping_price_from_so(self, orders):
        self.ensure_one()
        if self.delivery_type == 'dhl':
            return [0]

    delivery_type = fields.Selection(selection_add=[('dhl', "DHL")])

    dhl_user_id = fields.Char(string="DHL User ID", groups="base.group_system")
    dhl_password = fields.Char(string="DHL Password", groups="base.group_system")
    dhl_shipment_option = fields.Selection([('DOOR','Door')], default="DOOR", string="DHL Shipment Option", groups="base.group_system")
    dhl_parcel_type = fields.Selection([('SMALL','Small'),('MEDIUM','Medium'),('LARGE','Large'),('PALLET','Pallet')], default="SMALL", string="DHL Parcel Type")
    dhl_account_id = fields.Char(string="DHL Account ID", groups="base.group_system")