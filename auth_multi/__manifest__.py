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
    'name': 'OAuth2 Multi Login',
    'version': '11.0.0.1.0',
    'author': 'Vauxoo',
    'category': 'Hidden',
    'website': 'http://www.vauxoo.com',
    'license': 'LGPL-3',
    'depends': [
        'web',
        'auth_oauth',
    ],
    'data': [
        'data/website_crm_data.xml',
        'security/log_security.xml',
        'security/ir.model.access.csv',
        'view/res_users_view.xml',
        'view/auth_view.xml',
        'wizard/merge_user_view.xml',
    ],
    'external_dependencies': {
        'python': [
            'simplejson']
    },
    'installable': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
    'web_preload': False,
}
