# -*- encoding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api


class ProductQuantity(models.TransientModel):
    _name = 'product.quantity'

    @api.model
    def default_get(self, fields):
        vals = super(ProductQuantity, self).default_get(fields)
        prod_obj = self.env['product.product']
        product_id = False
        if self._context.get('active_model') in ('sale.order.line', 'purchase.order.line'):
            record = self.env[self._context['active_model']].browse(self._context['active_id'])
            product_id = record.product_id and record.product_id.id or False
        if self._context.get('active_model') == 'product.template':
            product_tmpl_id = self._context.get('active_id', False)
            product_ids = prod_obj.search([('product_tmpl_id', '=', product_tmpl_id)])
            product_id = product_ids and product_ids[0].id or False
        if self._context.get('active_model') == 'product.product':
            product_id = self._context.get('active_id', False)
        if product_id:
            vals.update({'product_id': product_id})
        if product_id:
            warehouse_line = []
            self.env.cr.execute("""select
            location_id, sum(qty)
            from stock_quant  where
            product_id = %s and location_id in (select
            id
            from stock_location where
            usage = 'internal') group
            by
            location_id""" % (product_id))
            locations = self.env.cr.fetchall()
            for loc in locations:
                location = self.env['stock.location'].sudo().browse(loc[0])
                warehouse_line += [(0, 0, {
                    'location': location.complete_name.split('/', 1)[1],
                    'avail_qty': loc[1],
                })]

            vals.update({'lines': warehouse_line})
        return vals

    lines = fields.One2many('product.quantity.line', 'prod_qty_id', string="Product Qty")
    product_id = fields.Many2one('product.product', string="Product", readonly=True)


class ProductQuantityLine(models.TransientModel):
    _name = 'product.quantity.line'

    prod_qty_id = fields.Many2one('product.quantity', string="Warehouse Product")
    location = fields.Char()
    avail_qty = fields.Char("Available Qty")
