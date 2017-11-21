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
import re
from odoo import tools, models, api, _, fields
from odoo.exceptions import UserError
from odoo.addons.mail.models.mail_template import mako_template_env
from odoo.tools.safe_eval import safe_eval


class MergeUserForLoginLine(models.Model):
    _name = 'merge.user.for.login.line'

    same_email = fields.Boolean(help='To identify if this '
                                'line has the same email')
    user_id = fields.Many2one('res.users', 'Main User',
                              help='Main users, result of all '
                                   'process')
    login = fields.Many2one('merge.user.for.login')
    authorized = fields.Boolean(help='True if this line was authorized')


class MergeUserForLogin(models.Model):
    _name = 'merge.user.for.login'
    _description = 'Merge Login'

    executed = fields.Boolean(help='True if this line was merged')
    message = fields.Text(help='Info about search')
    search_c = fields.Char('Value to Search',
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
                            help='Type of value to search to '
                            'determinate if an user is duplicated')
    access_token = fields.Char()

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
        return token.decode()

    @api.model
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
                       'oauth_provider_id': user_brw.oauth_provider_id.id,
                       'oauth_uid': user_brw.oauth_uid,
                       'oauth_access_token': user_brw.oauth_access_token})],
                    'oauth_provider_id': False,
                    'oauth_uid': False,
                    'oauth_access_token': False,
                })
        return True

    @api.model
    def send_emails(self, main_id, user_id, action, res_id):
        """ Send an email to ask permission to do merge with users that have the
        same email account
        :param user_id: User id that receives the notification mail
        :param action_id: String with the token of the record created
        :param res_id: Id of record created to do merge
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
                    render(
                        {'r':
                         {'message': _('Process Completed'),
                          'request': _(
                              'Process finished the users were merged')}})
                self.update({'message': body})
                return True

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
        :type: String with the field used to find user, this may be name or
        email
        :param: String with the name or email used to find user with same
        Criteria
        @user: User ID of the main user
        return all user found and a message reporting it
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
                                  'request': _('The value filled out '
                                               'in the field '
                                               'was not found, please '
                                               'check it and try again')}})
                res['value'] = {'message': body}

        for i in self.user_ids:
            if i and i[0] == 0 and not i[2].get('user_id', 0) in users:
                user += [i[2]]
        res['value'].update({'user_ids': user})

        self.update(res.get('value'))

    @api.multi
    def execute_merge(self):
        """ Execute the merge if all users involved allow this change else show a
        message reporting
        why you can't do it
        """
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
            authorized = [i.authorized for i in merge_brw.user_ids]
            if all(authorized):
                user_ids = [i.user_id.id for i in merge_brw.user_ids]
                self.merge_records('res_users', parent_brw.id, user_ids,
                                   'res.users')
                merge_brw.write({
                    'executed': True
                })
                return True
            return any(authorized)

        return False

    def merge_records(self, table, main_id, old_ids, orm_model):
        """Method used to merge records in all tables with
        a reference to the objects to merge
        :param tabel: Table name of the records to merge. i.e. res_users
        :type tabel: str
        :param main_id: Id of the main record, this id will replace the other
                        ids in the tables related
        :type main_id: integer
        :param old_ids: List  with the ids of the records to merge
        :type old_ids: list or tuple
        :param orm_model: Name of the model for the orm. i.e. res.users
        :type orm_model: str
        """

        self._cr.execute('''
DROP FUNCTION IF EXISTS merge_records(model_name varchar, main_id integer,
                                      old_ids integer[], orm_model varchar);
CREATE OR REPLACE FUNCTION merge_records(model_name varchar, main_id integer,
                                         old_ids integer[], orm_model varchar)
RETURNS float AS $$
    DECLARE

        value_table varchar;
        value_column varchar;
        values RECORD;
        proper_id integer;
        record_id integer;
        amount float;
    BEGIN
        FOR value_table, value_column IN SELECT cl1.relname as table,
                             att1.attname as column
                      FROM pg_constraint as con, pg_class as cl1,
                           pg_class as cl2, pg_attribute as att1,
                           pg_attribute as att2
                      WHERE con.conrelid = cl1.oid
                           AND con.confrelid = cl2.oid
                           AND array_lower(con.conkey, 1) = 1
                           AND con.conkey[1] = att1.attnum
                           AND att1.attrelid = cl1.oid
                           AND cl2.relname = model_name
                           AND att2.attname = 'id'
                           AND array_lower(con.confkey, 1) = 1
                           AND con.confkey[1] = att2.attnum
                           AND att2.attrelid = cl2.oid
                           AND con.contype = 'f' LOOP

            UPDATE
                ir_property
            SET
                res_id = orm_model|| ',' || main_id
            WHERE
                split_part(res_id, ',', 1) = orm_model
                AND split_part(res_id, ',', 2)::integer = ANY(old_ids);

            UPDATE
                ir_property
            SET
                value_reference = orm_model|| ',' || main_id
            WHERE
                split_part(value_reference, ',', 1) = orm_model AND
                split_part(value_reference, ',', 2)::integer = ANY(old_ids);

            BEGIN
                EXECUTE 'UPDATE ' || value_table ||
                        ' SET ' || value_column || ' = ' || main_id ||
                        ' WHERE ' || value_column || ' = ANY('
                            || quote_literal(old_ids) || ')';

            EXCEPTION WHEN unique_violation THEN
                FOREACH record_id SLICE 0 IN ARRAY old_ids LOOP
                    BEGIN
                        EXECUTE 'UPDATE ' || value_table ||
                                ' SET ' || value_column || ' = ' || main_id ||
                                ' WHERE ' || value_column || ' = '
                                    || record_id;

                    EXCEPTION WHEN unique_violation THEN
                        -- Ignore duplicate inserts.
                        amount := 1;
    /* RAISE NOTICE USING MESSAGE='Unique Constraint Error '|| value_table; */
                    END;
                END LOOP;
            END;
            UPDATE
                mail_message
            SET
                res_id = main_id
            WHERE
                model = orm_model AND res_id = ANY(old_ids);

            UPDATE
                ir_attachment
            SET
                res_id = main_id
            WHERE
                res_model = orm_model AND res_id = ANY(old_ids);
        END LOOP;
        RETURN amount; END;
    $$ LANGUAGE plpgsql;''')
        old_ids_str = re.sub(r'^(\(|\[)', '{', str(old_ids))
        old_ids_str = re.sub(r'(\)|\])$', '}', old_ids_str)

        self._cr.execute('SELECT merge_records(CAST(%s AS varchar),'
                         '%s, %s, CAST(%s AS varchar))',
                         (table, main_id, old_ids_str, orm_model))
