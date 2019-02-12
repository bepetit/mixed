# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Connector Transus - Stock Picking Send',
    'summary': 'Transus connection for pickings.',
    'license': 'AGPL-3',
    'author': 'Onestein',
    'website': 'http://www.onestein.eu',
    'category': 'Warehouse',
    'version': '10.0.1.0.0',
    'depends': [
        'stock',
        'transus',
    ],
    'data': [
        'templates/transus.xml',
        'views/res_partner_view.xml',
    ],
}
