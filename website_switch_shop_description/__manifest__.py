# -*- coding: utf-8 -*-
{
    # Module info
    'name': 'Website Switch Shop Description add fields',
    'version': '1.3.2',
    'category': 'website',
    'sequence': 1,
    'summary': 'Switch the description of the shop for product and add fields for product.',
    'description': """Switch the description of website and sale. Also add new fields for products, to be displayed on the website.""",

    # Author
    'author': 'Business Agility Masters',
    'website': 'https://www.businessagilitymasters.com',

    # Dependencies
    'depends': ['website_sale'],

    # Views
    'data': [
        'views/product.xml',
        'views/views.xml',
        'security/ir.model.access.csv',
    ],

    # Technical Specif.
    'installable': True,
    'application': False,
    'auto_install': False,
}