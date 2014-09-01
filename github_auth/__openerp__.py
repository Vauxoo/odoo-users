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
    'name' : 'Github Auth',
    'version' : '0.1',
    'author' : 'Vauxoo',
    'category' : 'Hidden',
    'description' : """
Auth wit Github API
===================

When you configure this, please use this configuration for the new oAuth provider:

.. image:: /github_auth/static/src/doc/odoo_config.png

And use this configuration on github:

.. image:: /github_auth/static/src/doc/github_config.png

Note that the client_id and key are provided by github.

    """,
    'website': 'http://www.vauxoo.com',
    'images' : [],
    'depends' : [
        'auth_oauth',
        'auth_signup',
    ],
    'data': [
        'data/auth_oauth_data.xml',
        'view/auth_oauth_view.xml',
    ],
    'js': [
    ],
    'qweb' : [
    ],
    'css':[
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'web_preload': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

