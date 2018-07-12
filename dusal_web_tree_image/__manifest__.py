# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Therp BV (<http://therp.nl>).
#
#    Snippet from https://github.com/hsd/listview_images
#    Copyright (C) 2013 Marcel van der Boom <marcel@hsdev.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Show images in tree views",
    "version": "2.5",
    "author": "Dusal Solutions,Therp BV,Odoo Community Association (OCA)",
    'support': 'almas@dusal.net',
    'url': 'https://github.com/OCA/Web',
    'license': 'AGPL-3',
    'category': 'Web',
    'sequence': 6,
    'images': ['static/images/main_screenshot.png'],
    'depends': [
        'web',
    ],

    'data': [
        'view/assets.xml',
    ],
    'qweb': [
        'static/src/xml/widget.xml',
    ],
    'installable': True,
}
