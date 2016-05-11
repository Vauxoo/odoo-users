# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'name': 'Auth Multi Login',
    'version': '8.0.0.1.0',
    'author': 'Vauxoo',
    'category': 'Hidden',
    'website': 'http://www.vauxoo.com',
    'license': 'AGPL-3',
    'depends': [
        'web',
        'base',
        'auth_oauth',
        'merge_editing',
        'auth_signup',
    ],
    'data': [
        'data/website_crm_data.xml',
        'security/log_security.xml',
        'security/ir.model.access.csv',
        'view/res_users_view.xml',
        'view/auth_view.xml',
        'wizard/merge_user_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'web_preload': False,
}
