# -*- coding: utf-8 -*-
# © 2017 Today Mourad EL HADJ MIMOUNE @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    name = fields.Many2one('res.partner', index=True,)
