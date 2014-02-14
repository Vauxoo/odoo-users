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
    'name' : 'Auth Multi Login',
    'version' : '0.1',
    'author' : 'Vauxoo',
    'category' : 'Hidden',
    'description' : """
Auth Multi Login and Do User Merge Request
============================================

    This module added new fields in the user model to:
        1) Allow do login with multiple gmail accounts.
        2) Write log with changes in user groups.
        3) Work with the new gmail fields.
        
        
How to use
----------

    1) You need immediately installed the module change the old gmail fields to work with the new fiels that allow do login with multiples gmail account.
        
        1.1) There is a wizard to execute this change in user view
            .. image:: auth_multi/static/src/demo/Users-OpenERP.png
            .. image:: auth_multi/static/src/demo/Users-OpenERP-action.png
        
    2) Then you can do pre merge proposal from preference user view 
        .. image:: auth_multi/stati:c/src/demo/pre_merge1.png
        .. image:: auth_multi/static/src/demo/pre_merge2.png
        .. image:: auth_multi/static/src/demo/pre_merge3.png

        
    3) If the users found have the same mail that the main user the merge it will be automatically


    4) The mail with the merge request has a direct link to apply merge in the system, must be necessary that all user involved allow the merge

    5) Important Branch bzr branch lp:~josemoralesp/alce/mass_editing_7/
    """,
    'website': 'http://www.vauxoo.com',
    'images' : [],
    'depends' : [
        'web',
        'base',
        'auth_oauth',
        'merge_editing',
        'auth_signup',
    ],
    'data': [
        'security/log_security.xml',
        'security/ir.model.access.csv',
        'view/res_users_view.xml',
        'wizard/merge_user_view.xml',
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

