# coding=utf-8
{
    'name': "DHL - Print Customs Report",
    'description': "DHL - Print Customs Report for Non-EU country shippings.",
    'author': 'Business Agility Masters',
    'website': 'www.businessagilitymasters.com',
    'category': 'Warehouse',
    'version': '10.0.1.0.4',
    'license': 'AGPL-3',
    'depends': [
        'dhl_delivery_label',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/report_customer_invoice_dhl.xml',
        'views/account_invoice_report.xml',
        'views/stock_picking_modifier.xml',
    ],
}
