# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

import os
import binascii
from odoo import tools, models, api, _, fields
from odoo.exceptions import UserError
from odoo.addons.mail.models.mail_template import mako_template_env
from odoo.tools.safe_eval import safe_eval
import re


class MergeUserForLoginLine(models.Model):
    _name = 'merge.user.for.login.line'

    same_email = fields.Boolean('Same Email',
                                help='To identifed if this '
                                'line has the same email')
    user_id = fields.Many2one('res.users', 'Main User',
                              help='Main users, result of all '
                                   'process')
    login = fields.Many2one('merge.user.for.login', 'Login')
    authorized = fields.Boolean('Authorized',
                                help='True if this line was authorized')


class MergeUserForLogin(models.Model):
    _name = 'merge.user.for.login'
    _description = 'Merge Login'

    executed = fields.Boolean('Excecuted',
                              help='True if this line was merged')
    message = fields.Text('Message', help='Info about search')
    search_c = fields.Char('Criterial',
                           help='Name or  email to search')
    user_id = fields.Many2one('res.users', 'Main User',
                              default=lambda self: self.env.user,
                              help='Main users, result of all '
                              'process')
    user_ids = fields.One2many('merge.user.for.login.line',
                               'login', string='User to merge',
                               help='User will be merged')
    type = fields.Selection([('name', 'Name'),
                             ('email', 'Email')],
                            'Search Type',
                            default='email',
                            help='Criterial search to '
                            'determinate if an user is duplicated')
    access_token = fields.Char('Access Token')

    _rec_name = 'access_token'

    @api.model
    def random_token(self):
        """ Generates an ID to identify each one of record created
        return the strgin with record ID
        """
        # the token has an entropy of about 120 bits (6 bits/char * 20 chars)
        token = binascii.hexlify(os.urandom(20))
        if self.search([('access_token', '=', token)]):
            return self.random_token()
        return token

    @api.multi
    def change_gmail_fields(self):
        """ Originally for do login with google, we use only 3 fields that allow to
        login with one
        gmail account. But now we can do login with multiple gmail accounts,
        for that, this method
        change the values in old fields and sets these in the new fields used
        to do login with
        multiple gmail accounts
        """
        tokens_obj = self.env['oauth.tokens']
        user_obj = self.env['res.users']
        user_ids = user_obj.search([('oauth_provider_id', '!=', False)])
        for user_brw in user_ids:
            if not tokens_obj.search([('oauth_provider_id', '=',
                                       user_brw.oauth_provider_id.id),
                                      ('oauth_uid', '=', user_brw.oauth_uid),
                                      ('user_id', '=', user_brw.id)]):
                user_brw.write({
                    'oauth_tokens':
                    [(0, 0,
                      {'name': user_brw.login,
                       'oauth_provider_id': (user_brw.oauth_provider_id and
                                             user_brw.oauth_provider_id.id),
                       'oauth_uid': user_brw.oauth_uid,
                       'oauth_access_token': user_brw.oauth_access_token})]
                })
        return True

    @api.model
    def send_emails(self, main_id, user_id, action, res_id):
        """ Send an email to ask permission to do merge with users that have the
        same email account
        @param user_id: User id that receives the notification mail
        @param action_id: String with the token of the record created
        @param res_id: Id of record created to do merge
        """
        mail_mail = self.env['mail.mail']
        partner_obj = self.env['res.partner'].sudo()
        user_obj = self.env['res.users'].sudo()
        user = user_obj.browse(user_id)
        main_user = user_obj.browse(main_id)
        data_obj = self.env['ir.model.data']
        url = partner_obj.browse(user.partner_id.id).\
            _get_signup_url_for_action(action='',
                                       res_id=res_id,
                                       model='merge.user.for.login',).\
            get(user.partner_id.id)
        base_url = self.env['ir.config_parameter'].sudo().\
            get_param('web.base.url', default='')
        url = '%s/do_merge/execute_merge?token=%s' % (base_url, action)
        if not user.login:
            raise UserError(_('Email Required'),
                            _('The current user must have an '
                              'email address configured in '
                              'User Preferences to be able '
                              'to send outgoing emails.'))

        #  TODO: also send an HTML version of this mail
        email_to = user.login
        subject = user.name
        template_obj = data_obj.get_object('auth_multi',
                                           'merge_proposal_template')
        body = template_obj.body_html
        body_dict = {
            'r': {
                'tittle': _('Merge Proposal'),
                'access': _('Access to Merge'),
                'url': url,
                'base_url': base_url,
                'genereted': _('Generated By:'),
                'name': main_user.name,
                'message': _('If you are disagree ignore '
                             'this email Contact with your administrator'),
                'user': (_('Dear ') + user.name),
                'message2': _('You have a request to join this '
                              'user. If you agree do click '
                              'on the access link'),
            }
        }
        template = mako_template_env.from_string(tools.ustr(body))
        body = template.render(body_dict)
        mail_mail.create({
            'email_from': user.login,
            'email_to': email_to,
            'subject': subject,
            'body_html':  body}).send()
        # force direct delivery, as users expect instant notification
        return True

    @api.multi
    def do_pre_merge(self):
        user_obj = self.env['res.users']
        user_ids = user_obj.search([])
        wzr_brw = self

        # pylint: disable=W0612
        for user_brw in user_ids:
            users = user_obj.\
                search([('%s' % wzr_brw.type, 'ilike',
                         safe_eval('user_brw.%s' % wzr_brw.type))])
            if users:
                token = self.random_token()
                self.create({'access_token': token,
                             'user_id': users[0],
                             'user_ids': [(0, 0,
                                           {'user_id': i})
                                          for i in users]})
                self.send_emails(self._uid, users.ids[0], token)
        return True

    @api.multi
    def do_pre_merge_from_users(self):
        """ Send email to ask permission to do merge or do merge directly if the
        email of user to merge
        is the same of the main user
        """
        self.ensure_one()
        wzr_brw = self.sudo()
        parent_brw = wzr_brw.user_id
        body = '''
  <div cellspacing="10" style="font-family:verdana;background-color:#C6DEFF;">
      <div>Result:</div>
      <div>${r.get('message')}</div>
      <div>${r.get('request')}</div>
  </div>
        '''
        template = mako_template_env.from_string(tools.ustr(body))
        if wzr_brw.user_ids:
            if all([((i.user_id.login == parent_brw.login) or
                     (i.user_id.email == parent_brw.email)) and
                    True or False for i in wzr_brw.user_ids]):
                fuse_obj = self.env['merge.fuse.wizard'].sudo()
                user_ids = [i.user_id.id for i in wzr_brw.user_ids]
                user_ids.insert(0, parent_brw.id)
                fuse_obj.\
                    with_context({'active_model': 'res.users',
                                  'active_ids': user_ids}).create({})
                wzr_brw.write({
                    'executed': True
                })
                body = template.\
                    render({'r':
                            {'message': _('Process Completed'),
                             'request': _('Proccess finished users merged')}})
                self.update({'message': body})
            else:
                token = self.sudo().random_token()
                wzr_brw.write({
                    'access_token': token,
                    'user_ids': [(0, 0, {'user_id': wzr_brw.user_id.id})]
                })
                user_mails = []
                for i in wzr_brw.user_ids:
                    if i.user_id.id not in user_mails:
                        self.send_emails(self._uid, i.user_id.id, token,
                                         wzr_brw.id)
                    user_mails.append(i.user_id.id)
                if wzr_brw.user_id.id not in user_mails:
                    self.send_emails(self._uid, wzr_brw.user_id.id, token,
                                     wzr_brw.id)

    @api.onchange('user_id', 'type', 'search_c', 'user_ids')
    @api.multi
    def onchange_search(self):
        """ Search user with the same email sent from view and return the result or
        a message
        @type: String with the field used to find user, this may be name or
        email
        @param: String with the name or email used to find user with same
        Criterial
        @user: User ID of the main user
        return all user found and a messagen reporting it
        """
        user_obj = self.env['res.users']
        parent_brw = self.user_id
        user = []
        users = []
        res = {'value': {}}
        body = '''
  <div cellspacing="10" style="font-family:verdana;background-color:#C6DEFF;">
      <div>Result:</div>
      <div>${r.get('message')}</div>
      <div>${r.get('request')}</div>
  </div>
        '''
        template = mako_template_env.from_string(tools.ustr(body))
        # pylint: disable=W1401
        if self.search_c and self.type == 'email' and \
                re.match("[^@]+@[^@]+\.[^@]+", self.search_c) or self.search_c:
            users += user_obj.sudo().\
                search([('%s' % self.type, '=', self.search_c)]).ids
        # if line_obj.sudo().search([('user_id', 'in', users),
        #                            ('login.executed', '=', True)]) or \
        #         self.sudo().search([('user_id', 'in', users),
        #                     ('executed', '=', True)]):
        #     res['value'] = {
        #         'message': _('This user is being used in another '
        #                      'merge that is not validated yet')}
        #     self.update(res.get('value'))
        #     return res
        old_token = self.sudo().search([('user_id', 'in', users),
                                        ('executed', '=', False)])
        if old_token:
            old_token.unlink()

        users = list(set(users))
        if users:
            user += [{'user_id': i.id,
                      'same_email': (i.email == parent_brw.email and
                                     True or False)}
                     for i in user_obj.sudo().browse(users)]
            body = template.render({'r': {'message': _('User Found'),
                                          'request': _('Please press the Send '
                                                       'Mail button to send '
                                                       'the Merge request '
                                                       'for this user')}})
            res['value'] = {'message': body}
            res['value'].update({'user_ids': user})
        else:
            if self.search_c:
                body = template.\
                    render({'r': {'message': _('User not Found'),
                                  'request': _('The email placed in '
                                               'the criterial field '
                                               'was not found, please '
                                               'check it and try again')}})
                res['value'] = {'message': body}

        if self.user_ids:
            for i in self.user_ids:
                if i and i[0] == 0:
                    if not i[2].get('user_id', 0) in users:
                        user += [i[2]]
            res['value'].update({'user_ids': user})

        self.update(res.get('value'))

    @api.multi
    def execute_merge(self):
        """ Execute the merge if all users involved allow this change else show a
        message reporting
        why you can't do it
        """
        fuse_obj = self.env['merge.fuse.wizard']
        token = self._context.get('record', False)
        user_obj = self.env['res.users'].sudo()
        merge_ids = self._ids and self or \
            self.sudo().search([('access_token', '=', token)])
        merge_brw = merge_ids
        parent_brw = user_obj.browse(merge_brw.user_id.id)
        anony = True
        if not merge_brw.executed:
            for user in merge_brw.user_ids:
                if user.user_id.id == self._uid:
                    anony = False
                    user.write({'authorized': True})
                elif parent_brw.id == self._uid:
                    anony = False
            if anony:
                return (False, 'Login')
            merge_brw = merge_ids and merge_ids[0]
            if all([i.authorized for i in merge_brw.user_ids]):
                user_ids = [i.user_id.id for i in merge_brw.user_ids]
                fuse_id = fuse_obj.sudo().\
                    with_context({'active_model': 'res.users',
                                  'active_id': parent_brw.id,
                                  'active_ids': user_ids}).\
                    create({})
                fuse_id.merge_records('res_users', parent_brw.id, user_ids,
                                      'res.users')
                merge_brw.write({
                    'executed': True
                })
                return True

        return False
