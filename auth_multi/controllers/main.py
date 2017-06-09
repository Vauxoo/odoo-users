# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

# ----------------------------------------------------------
# Controller
# ----------------------------------------------------------


class AuthMutiLogin(http.Controller):

    @http.route(['/do_merge/execute_merge'],
                type='http', auth="user", website=True, multilang=True)
    def execute_merge(self, **post):
        values = {}
        public_user = request.env.ref('base.public_user')
        # if not given: subject is contact name
        if request.env.user == public_user:
            url = u'/do_merge/execute_merge?token=%s' % post.get('token')
            query = {'redirect': url}
            return http.local_redirect('/web/login', query=query)

        merge_login_obj = request.env['merge.user.for.login']
        merge_brw = merge_login_obj.sudo().search([('access_token', '=',
                                                    post.get('token'))])
        if merge_brw:
            if merge_brw.executed:
                values['process'] = 'used'
                values['message'] = 'Token Excecuted'

                return request.render(
                    "auth_multi.auth_multi_token_used", values)

            values['main_name'] = merge_brw.user_id.name
            values['same_user'] = (merge_brw.user_id == request.env.user)
            names = []
            for users in merge_brw.user_ids:
                names.append((users.user_id.name, users.authorized))
            values['users'] = names
            values['token'] = post.get('token')
        else:
            values['process'] = 'notfound'
            return request.render("auth_multi.auth_multi_token_used", values)

        return request.render("auth_multi.auth_multi_login", values)

    @http.route(['/do_merge/apply_merge'], type='http',
                auth="user", website=True, multilang=True)
    def apply_merge(self, **post):
        values = {}
        merge_login_obj = request.env['merge.user.for.login'].with_context(
            {'record': post.get('token')}
        )
        result = merge_login_obj.execute_merge()
        merge_brw = merge_login_obj.sudo().search(
            [('access_token', '=', post.get('token'))])
        if merge_brw:
            values['main_name'] = merge_brw.user_id.name
            names = []
            auth = []
            for users in merge_brw.user_ids:
                names.append(users.user_id.email)
                auth.append(users.authorized)
            values['auth'] = all(auth)
            values['process'] = 'error'
            values['message'] = 'Error'

        query = {'redirect': u'do_merge/execute_merge?token=%s'
                 % post.get('token')}
        return isinstance(result, tuple) and \
            http.local_redirect('/web/login', query=query) or \
            result and \
            http.local_redirect('/web/login', query={'redirect': '/'}) or \
            request.render("auth_multi.auth_multi_token_used", values)
