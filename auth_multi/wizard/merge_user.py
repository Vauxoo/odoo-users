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

from openerp.osv import osv, fields
from openerp.tools.translate import _
import random
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.addons.email_template.email_template import mako_template_env
import re
from openerp.addons.web import http
openerpweb = http


class merge_user_for_login_line(osv.Model):
    _name = 'merge.user.for.login.line'

    _columns = {

        'same_email': fields.boolean('Same Email',
                                     help='To identifed if this '
                                     'line has the same email'),
        'user_id': fields.many2one('res.users', 'Main User',
                                   help='Main users, result of all '
                                   'process'),
        'login': fields.many2one('merge.user.for.login', 'Login'),
        'authorized': fields.boolean('Authorized',
                                     help='True if this line was authorized'),

    }
    _defaults = {
        'authorized': False
    }


class merge_user_for_login(osv.Model):
    _name = 'merge.user.for.login'
    _description = 'Merge Login'

    _columns = {

        'executed': fields.boolean('Excecuted',
                                   help='True if this line was merged'),
        'message': fields.text('Message', help='Info about search'),
        'search_c': fields.char('Criterial',
                                help='Name or  email to search'),

        'user_id': fields.many2one('res.users', 'Main User',
                                   help='Main users, result of all '
                                        'process'),
        'user_ids': fields.one2many('merge.user.for.login.line',
                                    'login', string='User to merge',
                                    help='User will be merged'),
        'type': fields.selection([('name', 'Name'),
                                  ('email', 'Email')],
                                 'Search Type',
                                 help='Criterial search to '
                                 'determinate if an user is duplicated'),
        'access_token': fields.char('Access Token'),
    }

    _defaults = {
        'type': 'email'
    }

    _rec_name = 'access_token'

    def random_token(self, cr, uid, context=None):
        '''
        Generates an ID to identify each one of record created
        return the strgin with record ID
        '''
        context = context or {}
        # the token has an entropy of about 120 bits (6 bits/char * 20 chars)
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZab'\
            'cdefghijklmnopqrstuvwxyz0123456789'
        token = ''.join(random.choice(chars) for i in xrange(20))
        if self.search(cr, uid, [('access_token', '=', token)]):
            return self.random_token(cr, uid)
        else:
            return token

    def change_gmail_fields(self, cr, uid, ids, context=None):
        '''
        Originally for do login with google, we use only 3 fields that allow to
        login with one
        gmail account. But now we can do login with multiple gmail accounts,
        for that, this method
        change the values in old fields and sets these in the new fields used
        to do login with
        multiple gmail accounts

        '''
        context = context or {}
        tokens_obj = self.pool.get('gmail.tokens')
        user_obj = self.pool.get('res.users')
        user_ids = user_obj.search(cr, uid, [], context=context)
        for user_brw in user_obj.browse(cr, uid, user_ids, context=context):
            if not tokens_obj.search(cr, uid,
                                     [('oauth_provider_id', '=',
                                       user_brw.oauth_provider_id and
                                         user_brw.oauth_provider_id.id),
                                      ('oauth_uid', '=', user_brw.oauth_uid),
                                      ('user_id', '=', user_brw.id)],
                                     context=context):
                user_brw.write({
                    'gmail_tokens':
                    [(0, 0,
                      {
                          'name': user_brw.login,
                          'oauth_provider_id': user_brw.oauth_provider_id and
                          user_brw.oauth_provider_id.id,
                          'oauth_uid': user_brw.oauth_uid,
                          'oauth_access_token': user_brw.oauth_access_token})]
                })
        return True

    def send_emails(self, cr, uid, main_id, user_id, action, res_id,
                    context=None):
        '''
        Send an email to ask permission to do merge with users that have the
        same email account
        @param user_id: User id that receives the notification mail
        @param action_id: String with the token of the record created
        @param res_id: Id of record created to do merge
        '''
        mail_mail = self.pool.get('mail.mail')
        partner_obj = self.pool.get('res.partner')
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, user_id)
        main_user = user_obj.browse(cr, uid, main_id, context=context)
        data_obj = self.pool.get('ir.model.data')
        url = partner_obj.\
            _get_signup_url_for_action(cr, user.id,
                                       [user.partner_id.id],
                                       action='',
                                       res_id=res_id,
                                       model='merge.user.for.login',
                                       context=context)[user.partner_id.id]
        model, action_id = data_obj.\
            get_object_reference(cr, uid, 'auth_multi',
                                 'validate_merge_action')

        base_url = self.pool.get('ir.config_parameter').\
            get_param(cr, uid, 'web.base.url', default='', context=context)
        url = '%s/do_merge/execute_merge?token=%s' % (base_url, action)
        if not user.email:
            raise osv.except_osv(_('Email Required'),
                                 _('The current user must have an '
                                   'email address configured in '
                                   'User Preferences to be able '
                                   'to send outgoing emails.'))

        # TODO: also send an HTML version of this mail
        mail_ids = []
        email_to = user.email
        subject = user.name
        template_obj = data_obj.get_object(cr, uid, 'auth_multi',
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
        t = mako_template_env.from_string(tools.ustr(body))
        body = t.render(body_dict)
        mail_ids.append(mail_mail.create(cr, uid, {
            'email_from': user.email,
            'email_to': email_to,
            'subject': subject,
            'body_html':  body}, context=context))
        # force direct delivery, as users expect instant notification
        mail_mail.send(cr, uid, mail_ids, context=context)
        return True

    def do_pre_merge(self, cr, uid, ids, context=None):
        context = context or {}
        user_obj = self.pool.get('res.users')
        user_ids = user_obj.search(cr, uid, [], context=context)
        wzr_brw = self.browse(cr, uid, ids[0], context=context)

        for user_brw in user_obj.browse(cr, uid, user_ids, context=context):
            users = user_obj.search(cr, uid,
                                    [('%s' % wzr_brw.type, 'ilike',
                                      eval('user_brw.%s' % wzr_brw.type))],
                                    context=context)
            if users:
                token = self.random_token(cr, uid)
                self.create(cr, uid,
                            {
                                'access_token': token,
                                'user_id': users[0],
                                'user_ids': [(0, 0,
                                              {'user_id': i})
                                             for i in users]
                            })
                self.send_emails(cr, uid, uid, users[0], token)
        return True

    def do_pre_merge_from_users(self, cr, uid, ids, context=None):
        '''
        Send email to ask permission to do merge or do merge directly if the
        email of user to merge
        is the same of the main user
        '''
        context = context or {}
        user_obj = self.pool.get('res.users')
        wzr_brw = self.browse(cr, SUPERUSER_ID, ids[0], context=context)
        parent_brw = user_obj.browse(cr, SUPERUSER_ID, wzr_brw.user_id.id,
                                     context=context)
        if wzr_brw.user_ids:
            if all([((i.user_id.login == parent_brw.login) or
                     (i.user_id.email == parent_brw.email)) and
                    True or False for i in wzr_brw.user_ids]):
                fuse_obj = self.pool.get('merge.fuse.wizard')
                user_ids = [i.user_id.id for i in wzr_brw.user_ids]
                user_ids.insert(0, parent_brw.id)
                context.update({'active_model': 'res.users',
                                'active_ids': user_ids})
                fuse_obj.create(cr, SUPERUSER_ID, {}, context=context)
                wzr_brw.write({
                    'executed': True
                })
                cr.commit()
                context.update({'default_message':
                                ('''Proccess finished users merged''')})
                self.return_action(cr, uid, ids, context=context)
            else:
                token = self.random_token(cr, SUPERUSER_ID)
                wzr_brw.write({
                    'access_token': token,
                    'user_ids': [(0, 0,
                                 {'user_id': wzr_brw.user_id.id})]
                })
                cr.commit()
                for i in wzr_brw.user_ids:
                    self.send_emails(cr, SUPERUSER_ID, uid, i.user_id.id,
                                     token, wzr_brw.id)
                self.send_emails(cr, SUPERUSER_ID, uid, wzr_brw.user_id.id,
                                 token, wzr_brw.id)
        return True

    def return_action(self, cr, uid, ids, context=None):
        context = context or {}
        data_obj = self.pool.get('ir.model.data')
        model, action_id = data_obj.\
            get_object_reference(cr, uid, 'auth_multi',
                                 'show_message_in_merge_action')
        model, view_id = data_obj.\
            get_object_reference(cr, uid, 'auth_multi',
                                 'show_message_in_merge_view_form')
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'merge.user.for.login',
            'views': [(view_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'inline',
            'context': context
        }

    def onchange_search(self, cr, uid, ids, type, param, user, lines,
                        context=None):
        '''
        Search user with the same email sent from view and return the result or
        a message
        @type: String with the field used to find user, this may be name or
        email
        @param: String with the name or email used to find user with same
        Criterial
        @user: User ID of the main user
        return all user found and a messagen reporting it
        '''
        context = context or {}
        user_obj = self.pool.get('res.users')
        line_obj = self.pool.get('merge.user.for.login.line')
        parent_brw = user_obj.browse(cr, SUPERUSER_ID, user, context=context)
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
        t = mako_template_env.from_string(tools.ustr(body))

        if param and type == 'email' and \
                re.match("[^@]+@[^@]+\.[^@]+", param) or param:
            users += user_obj.search(cr, SUPERUSER_ID, [('%s' % type, '=',
                                                         param)],
                                     context=context)
        if self.search(cr, SUPERUSER_ID, [('user_id', 'in', users),
                                          ('executed', '=', False)], context=context) or \
                line_obj.search(cr, SUPERUSER_ID,
                                [('user_id', 'in', users),
                                 ('login.executed', '=', False)],
                                context=context):
            res['value'] = {
                'message': _('This user is being used in another '
                             'merge that is not validated yet')}
            return res
        users = list(set(users))
        if users:
            user += [{'user_id': i.id,
                      'same_email': i.email == parent_brw.email and
                      True or False}
                     for i in user_obj.browse(cr, SUPERUSER_ID, users)]
            body = t.render({'r': {'message': _('User Found'),
                                   'request': _('Please press the Send '
                                                'Mail button to send '
                                                'the Merge request '
                                                'for this user')
                                   }})
            res['value'] = {'message': body}
            res['value'].update({'user_ids': user})
        else:
            if param:
                body = t.render({'r': {'message': _('User not Found'),
                                       'request': _('The email placed in '
                                                    'the criterial field '
                                                    'was not found, please '
                                                    'check it and try again')
                                       }})
                res['value'] = {'message': body}

        if lines:
            for i in lines:
                if i and i[0] == 0:
                    if not i[2].get('user_id', 0) in users:
                        user += [i[2]]
            res['value'].update({'user_ids': user})

        return res

    def execute_merge(self, cr, uid, ids, context=None):
        """
        Execute the merge if all users involved allow this change else show a
        message reporting
        why you can't do it
        """
        context = context or {}
        fuse_obj = self.pool.get('merge.fuse.wizard')
        token = context.get('record', False)
        user_obj = self.pool.get('res.users')
        merge_ids = ids or self.search(cr, SUPERUSER_ID, [('access_token', '=',
                                                           token)],
                                       context=context)
        merge_brw = merge_ids and self.browse(cr, SUPERUSER_ID, merge_ids[0],
                                              context=context)
        parent_brw = user_obj.browse(cr, SUPERUSER_ID, merge_brw.user_id.id,
                                     context=context)
        anony = True
        if not merge_brw.executed:
            for user in merge_brw.user_ids:
                if user.user_id.id == uid:
                    anony = False
                    user.write({'authorized': True})
                    cr.commit()
                elif parent_brw.id == uid:
                    anony = False
            if anony:
                return (False, 'Login')

                raise osv.except_osv(_('Error'),
                                     _('You need be logged '
                                       'in the system'))

            merge_brw = merge_ids and \
                self.browse(cr, SUPERUSER_ID, merge_ids[0], context=context)
            if all([i.authorized for i in merge_brw.user_ids]):
                fuse_obj = self.pool.get('merge.fuse.wizard')
                user_ids = [i.user_id.id for i in merge_brw.user_ids]
                user_ids.insert(0, parent_brw.id)
                context.update({'active_model': 'res.users',
                                'active_ids': user_ids})
                fuse_obj.create(cr, SUPERUSER_ID, {}, context=context)
                merge_brw.write({
                    'executed': True
                })
                cr.commit()
                context = {'default_message': _('''Proccess finished
                                                users merged''')}
                return True
            else:
                context = {'default_message': _('You need permmision of '
                                                'others users to do '
                                                'this merge')}
                return False

        return False
