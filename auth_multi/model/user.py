# coding: utf-8
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

import simplejson

from odoo import api, models, fields
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class OauthTokens(models.Model):

    _name = 'oauth.tokens'

    name = fields.Char('Login',
                       help='User login for your account')
    oauth_provider_id = fields.Many2one('auth.oauth.provider',
                                        'OAuth Provider')
    oauth_uid = fields.Char('OAuth User ID',
                            help="Oauth Provider user_id")
    oauth_access_token = fields.Char('OAuth Access Token', readonly=True)
    user_id = fields.Many2one('res.users', 'Users',
                              help='Reference Object')

    _sql_constraints = [('tokens_unique',
                         'unique(oauth_provider_id, '
                         'oauth_uid, oauth_access_token, user_id)',
                         'The email already have been set in another user')]


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def _search_my_contacs(self):
        partner_obj = self.env['res.partner']
        for user_brw in self:
            partner_id = user_brw.partner_id and user_brw.partner_id.id
            partner_ids = partner_obj.\
                search([('parent_id', '=', partner_id)])
            user_brw.my_contacts = partner_ids.ids

    oauth_tokens = fields.One2many('oauth.tokens', 'user_id',
                                   'oauth Access',
                                   help='Tokens that allow '
                                   'do login with many Oauth APIs')
    my_contacts = fields.One2many('res.partner',
                                  compute='_search_my_contacs',
                                  string='My Contacts',
                                  help='All my Contacts Partner')

    @api.multi
    def check_token_exist(self, values):
        """Check if token exist with the new model that contain all token allowed
        by an user
        @param ids: List with user ids
        @param values: Dictionary with the values necessary to login in the
        system
        return True if the token sent in values exist else return False
        """
        oauth_tokens_obj = self.env['oauth.tokens']
        for user in self:
            tokens_ids = oauth_tokens_obj.\
                search([('oauth_provider_id', '=',
                         values.get('oauth_provider_id')),
                        ('oauth_uid', '=', values.get('oauth_uid')),
                        ('user_id', '=', user.id),
                        ('oauth_access_token', '=',
                         values.get('oauth_access_token'))])
            return bool(tokens_ids)

    @api.model
    def check_credentials(self, password):
        """ Verifies that token is allowed by the user that tries do login
        @param password: String with the token sent
        """
        token_obj = self.env['oauth.tokens']

        try:
            return super(ResUsers, self).check_credentials(password)
        except AccessDenied:
            res = token_obj.sudo().\
                search([('user_id', '=', self._uid),
                        ('oauth_access_token', '=', password)])
            if not res:
                raise

    @api.model
    def _signup_create_user(self, values):
        """ Tries to create a new user but first search if any user has a email
        with the login that
        tries do login, if this exist verifies that has allowed the token sent
        in the method and
        return the user_id.
        If not exist, we create a new user with the values sent
        @param values: Dictionary with the user information to search or create
        return the user id found or created
        """
        user_ids = self.search(['|',
                                ('login', '=', values.get('login')),
                                ('email', '=', values.get('login'))])
        if user_ids:
            result = user_ids.check_token_exist(values)
            user_brw = user_ids[0]

            if not result:
                values.update({
                    'oauth_tokens': [(0, 0, {
                        'name': values.get('login', False),
                        'oauth_provider_id': values.pop('oauth_provider_id',
                                                        False),
                        'oauth_uid': values.pop('oauth_uid', False),
                        'oauth_access_token': values.pop('oauth_access_token',
                                                         False)
                    })]
                    })
                values.update({'login': user_brw.login})
                user_brw.write(values)
                return user_ids.ids[0]

            return user_ids.ids[0]

        else:
            values.update({
                'oauth_tokens': [(0, 0, {
                    'name': values.get('login', False),
                    'oauth_provider_id': values.pop('oauth_provider_id',
                                                    False),
                    'oauth_uid': values.pop('oauth_uid', False),
                    'oauth_access_token': values.pop('oauth_access_token',
                                                     False)
                })]
                })

        return super(ResUsers, self)._signup_create_user(values)

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        """ retrieve and sign in the user corresponding to provider and
        validated access token
            :param provider: oauth provider id (int)
            :param validation: result of validation of access token (dict)
            :param params: oauth parameters (dict)
            :return: user login (str)
            :raise: openerp.exceptions.AccessDenied if signin failed

            This method can be overridden to add alternative signin methods.
        """

        oauth_uid = validation['user_id']
        token_obj = self.env['oauth.tokens']
        token_ids = token_obj.\
            search([("oauth_uid", "=", oauth_uid),
                    ('oauth_provider_id', '=', provider)])

        if not token_ids:
            if self._context and self._context.get('no_user_creation'):
                return None
            state = simplejson.loads(params['state'])
            token = state.get('t')
            oauth_uid = validation['user_id']
            email = validation.get('email',
                                   'provider_%s_user_%s'
                                   % (provider, oauth_uid))
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
                _, login, _ = self.signup(values, token)
            except AccessDenied, access_denied_exception:
                raise access_denied_exception

        else:
            token_brw = token_ids[0]
            user = token_brw.user_id
            login = user.login

            token_brw.write({'oauth_access_token': params['access_token']})
        return login

    @api.multi
    def write(self, vals):
        """Overwrite to create a log with the changes in user groups
        """
        log_obj = self.env['user.log.groups']

        group = False
        for i in vals.keys():
            if 'group' in i:
                group = True
                break

        if group:
            for record in self:
                groups = record.read(['groups_id'])
                groups = groups and isinstance(groups, list) and \
                    groups[0] or groups
                log_obj.create({
                    'name': record.id,
                    'date': time.strftime('%Y-%m-%d %H:%m:%S'),
                    'group_ids': [(6, 0,
                                   groups.get('groups_id',
                                              []))]})

        return super(ResUsers, self).write(vals)

    @api.multi
    def search_users_for_merge(self):
        """ Return a view with do the merge request
        """
        action_id = self.env['ir.model.data'].\
            get_object_reference('auth_multi',
                                 'search_user_merge_action')
        action = self.env['ir.actions.act_window'].\
            with_context({'default_user_id': self._uid}).\
            browse(action_id[1]).\
            read([])
        copy_dict = dict(self._context).update({'default_user_id': self._uid})
        action = action[0]
        action.update({'context': copy_dict})

        return action


class UserLogGroups(models.Model):

    _name = 'user.log.groups'

    name = fields.Many2one('res.users', 'User',
                           help='Users with changes in their groups')
    date = fields.Datetime('Date',
                           help='Date of last change in the groups')
    group_ids = fields.Many2many('res.groups',
                                 'log_groups_users_rel',
                                 'uid', 'gid',
                                 'Groups')
