# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010 Vauxoo - http://www.vauxoo.com/
#    All Rights Reserved.
#    info Vauxoo (info@vauxoo.com)
############################################################################
#    Coded by: Luis Torres (luis_t@vauxoo.com)
############################################################################
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
import logging
import time

import urllib
import urlparse
import urllib2
import simplejson

import openerp
from openerp.addons.auth_signup.res_users import SignupError
from openerp.osv import osv, fields
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class gmail_tokens(osv.Model):
    
    _name = 'gmail.tokens'
    
    _columns = {
        'name':fields.char('Login', 64, help='User login for your gmail account'), 
            
        'oauth_provider_id': fields.many2one('auth.oauth.provider', 'OAuth Provider'),                 
        'oauth_uid': fields.char('OAuth User ID', help="Oauth Provider user_id"),                      
        'oauth_access_token': fields.char('OAuth Access Token', readonly=True),            
        'user_id':fields.many2one('res.users', 'Users', help='Reference Object'), 
        
            }
    _sql_constraints = [('tokens_unique',
                         'unique(oauth_provider_id, oauth_uid, oauth_access_token, user_id)',
                         'The email already have been set in another user')]

class res_users(osv.Model):
    _inherit = 'res.users'

#    def _search_my_sales(self, cr, uid, ids, name, args, context=None):
#        context = context or {}
#        sale_obj = self.pool.get('sale.order')
#        res = {}
#        for user_brw in self.browse(cr, uid, ids, context=context):
#            sale_ids = sale_obj.search(cr, uid, [('user_id', '=', user_brw.id)], context=context)
#            res.update({user_brw.id: sale_ids})
#        return res
    def _search_my_contacs(self, cr, uid, ids, name, args, context=None):
        context = context or {}
        partner_obj = self.pool.get('res.partner')
        res = {}
        for user_brw in self.browse(cr, uid, ids, context=context):
            partner_id = user_brw.partner_id and user_brw.partner_id.id
            partner_ids = partner_obj.search(cr, uid, [('parent_id', '=', partner_id)],
                                             context=context)
            res.update({user_brw.id: partner_ids})
        return res
    

    _columns = {
            'gmail_tokens':fields.one2many('gmail.tokens', 'user_id', 'Gmail Access',
                                           help='Tokens that allow do login with many '
                                                'google accounts'), 
           # 'my_own_sale':fields.function(_search_my_sales, method=True, string='My Sale Orders',
           #                               type='many2many',
           #                               relation='sale.order',
           #                               help='All my Sale Orders'), 
            'my_contacts':fields.function(_search_my_contacs, method=True, string='My Contacts',
                                          type='one2many',
                                          relation='res.partner',
                                          help='All my Contacts Partner'), 
            
            }


    def check_token_exist(self, cr, uid, ids, values, context=None):
        '''
        Check if token exist with the new model that contain all token allowed by an user
        @param ids: List with user ids
        @param values: Dictionary with the values necessary to login in the system
        return True if the token sent in values exist else return False
        '''
        context = context or {}
        gmail_tokens_obj = self.pool.get('gmail.tokens')
        if ids:
            tokens_ids = gmail_tokens_obj.search(cr, uid,
                                                 [('oauth_provider_id', '=',
                                                                  values.get('oauth_provider_id')),
                                                  ('oauth_uid', '=', values.get('oauth_uid')),
                                                  ('user_id', '=', ids[0]),
                                                  ('oauth_access_token', '=',
                                                                 values.get('oauth_access_token')),
                                                  ], context=context)
            if tokens_ids:
                return True

            else:
                return False
            
        return False

    def check_credentials(self, cr, uid, password):
        '''
        Verifies that token is allowed by the user that tries do login 
        @param password: String with the token sent
        '''
        token_obj = self.pool.get('gmail.tokens')
        
        try:
            return super(res_users, self).check_credentials(cr, uid, password)
        except openerp.exceptions.AccessDenied:
            res = token_obj.search(cr, SUPERUSER_ID, [('user_id', '=', uid), ('oauth_access_token', '=', password)])
            if not res:
                raise
    def _signup_create_user(self, cr, uid, values, context=None):
        '''
        Tries to create a new user but first search if any user has a email with the login that
        tries do login, if this exist verifies that has allowed the token sent in the method and
        return the user_id.
        If not exist, we create a new user with the values sent
        @param values: Dictionary with the user information to search or create
        return the user id found or created
        '''
        context = context or {}
        user_ids  = self.search(cr, uid, [('email', '=', values.get('login'))], context=context)
        if user_ids :
            result = self.check_token_exist(cr, uid, user_ids, values)
            user_brw = self.browse(cr, uid, user_ids[0], context=context)
            
            if not result:
                values.update({
                               'gmail_tokens':[(0, 0, {
                                   'name': values.get('login', False),
                                   'oauth_provider_id': values.pop('oauth_provider_id', False),
                                   'oauth_uid': values.pop('oauth_uid', False),
                                   'oauth_access_token': values.pop('oauth_access_token', False),
                                               })]
                    })
                values.update({'login': user_brw.login})
                self.write(cr, uid, user_ids[0], values, context=context)
                cr.commit()
                return user_ids[0]

            else:

                return user_ids[0]
        else:
            values.update({
                           'gmail_tokens':[(0, 0, {
                               'name': values.get('login', False),
                               'oauth_provider_id': values.pop('oauth_provider_id', False),
                               'oauth_uid': values.pop('oauth_uid', False),
                               'oauth_access_token': values.pop('oauth_access_token', False),
                                           })]
                })

        return super(res_users, self)._signup_create_user(cr, uid, values, context=context)
            

    def _auth_oauth_signin(self, cr, uid, provider, validation, params, context=None):
        """ retrieve and sign in the user corresponding to provider and validated access token
            :param provider: oauth provider id (int)
            :param validation: result of validation of access token (dict)
            :param params: oauth parameters (dict)
            :return: user login (str)
            :raise: openerp.exceptions.AccessDenied if signin failed

            This method can be overridden to add alternative signin methods.
        """
        context = context or {}
        
        oauth_uid = validation['user_id']                                                              
        token_obj = self.pool.get('gmail.tokens')
        token_ids = token_obj.search(cr, uid, [("oauth_uid", "=", oauth_uid),
                                               ('oauth_provider_id', '=', provider)])
        
        if not token_ids:                                                                               
            if context and context.get('no_user_creation'):                                            
                return None                                                                            
            state = simplejson.loads(params['state'])                                                  
            token = state.get('t')                                                                     
            oauth_uid = validation['user_id']                                                          
            email = validation.get('email', 'provider_%s_user_%s' % (provider, oauth_uid))             
            name = validation.get('name', email)                                                       
            values = {                                                                                 
                'name': name,                                                                          
                'login': email,                                                                        
                'email': email,                                                                        
                'oauth_provider_id': provider,                                                         
                'oauth_uid': oauth_uid,                                                                
                'oauth_access_token': params['access_token'],                                          
                'active': True,                                                                        
            }                                                                                          

            try:                                                                                       
                _, login, _ = self.signup(cr, uid, values, token, context=context)                     
            except SignupError:                                                                        
                raise access_denied_exception

        else:
            token_brw = token_obj.browse(cr, uid, token_ids[0], context=context)                                      
            user = token_brw.user_id
            login = user.login
        
            token_brw.write({'oauth_access_token': params['access_token']})                                     
        return login

    def write(self, cr, uid, ids, vals, context=None):
        '''
        Overwrite to create a log with the changes in user groups
        '''
        context = context or {}
        log_obj = self.pool.get('user.log.groups')
        
        group = False
        for i in vals.keys():
            if 'group' in i:
                group = True
                break

        if group:
            for id in ids:
                groups = self.read(cr, uid, id, ['groups_id'], context=context)
                log_obj.create(cr, uid, {'name':id,
                                         'date':time.strftime('%Y-%m-%d %H:%m:%S'),
                                         'group_ids':[(6, 0, groups.get('groups_id', []))],
                                         }, context=context)

        return super(res_users, self).write(cr, uid, ids, vals, context=context)
            
    def search_users_for_merge(self, cr, uid, ids, context=None):
        '''
        Return a view with do the merge request
        '''
        context = context or {}
        context.update({'default_user_id':uid})
        model, action_id = self.pool.get('ir.model.data').get_object_reference(cr, uid,
                                                                               'auth_multi',
                                                                               'search_user_merge_action')
        action = self.pool.get('ir.actions.act_window').read(cr, uid, action_id, [], context)
        action.update({'context':context})
        
        
        return action    
class user_log_groups(osv.Model):
    
    
    _name = 'user.log.groups'
    
    _columns = {
          'name':fields.many2one('res.users', 'User', help='Users with changes in their groups'), 
          'date':fields.datetime('Date', help='Date of last change in the groups'), 
          'group_ids': fields.many2many('res.groups', 'log_groups_users_rel', 'uid', 'gid',
                                        'Groups'),
            }
