# -*- coding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Warehouse wise Product Quantity on Sale and Purchase',
    'version': '1.0',
    'license': "AGPL-3",
    'category': 'Sales',
    'summary': 'Product Quantities on sale/purchase lines',
    'description': """
Check product Quantities on sale & purchase
==================================

Easily check OnHand, Incoming, Outgoing & Forecasted product quantities present in multi warehouse on sale/purchase lines and product. 
    """,
    'author': 'Yahvitech',
    'website': 'http://www.yahvitech.com',
    'depends': ['sale', 'purchase'],
    'data': [
        'wizard/wizard_warehouse_qty_view.xml',
        'views/product_view.xml',
        'views/sale_view.xml',
        'views/purchase_view.xml',
    ],
    'price': 30,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
