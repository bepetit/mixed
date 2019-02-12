# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Connector Transus - Invoice Receive',
    'summary': 'Transus connection for customer invoices and vendor bills.',
    'license': 'AGPL-3',
    'author': 'Onestein',
    'website': 'http://www.onestein.eu',
    'category': 'Accounting',
    'version': '10.0.1.0.0',
    'depends': [
        'account',
        # 'product_gtin', # TODO is it needed? GTIN is required for invoice lines
        'transus',
    ],
    'data': [
    ],
}
