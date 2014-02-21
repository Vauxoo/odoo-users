from openerp.addons.web import http                                                                    
from openerp.addons.web.http import request
import openerp.addons.web.controllers.main as webmain
from openerp import SUPERUSER_ID
import openerp
from openerp import SUPERUSER_ID

from urllib import quote_plus

openerpweb = http


#----------------------------------------------------------
# Controller
#----------------------------------------------------------
class auth_muti_login(openerpweb.Controller):

    @http.route(['/do_merge/execute_merge'], type='http', auth="public", website=True, multilang=True)
    def execute_merge(self, **post):
        cr, uid, context= request.cr, request.uid, request.context
        uid = SUPERUSER_ID
        values = {}
        public_user = request.registry['ir.model.data'].get_object(cr, uid, 'base', 'public_user')
        # if not given: subject is contact name
        if uid == public_user.id:
            url = u'/do_merge/execute_merge?token=%s' % post.get('token')
            query = {'redirect': url}
            return http.local_redirect('/web/login', query=query) 

        merge_login_obj = request.registry['merge.user.for.login']
        merge_ids = merge_login_obj.search(cr, uid, [('access_token', '=', post.get('token'))],
                                           context=context)
        if merge_ids:
            merge_brw = merge_login_obj.browse(cr, uid, merge_ids[0], context=context)
            if merge_brw.executed:
                values['process'] = 'used'
                values['message'] = 'Token Excecuted'
        
                return request.website.render("auth_multi.auth_multi_token_used", values)

            values['main_name'] = merge_brw.user_id.name
            values['same_user'] = (merge_brw.user_id.id == uid)
            names = []
            for users in merge_brw.user_ids:
                names.append((users.user_id.name, users.authorized))
            values['users'] = names
            values['token'] = post.get('token') 
        
        return request.website.render("auth_multi.auth_multi_login", values) 

    @http.route(['/do_merge/apply_merge'], type='http', auth="public", website=True, multilang=True)
    def apply_merge(self, **post):
        cr, uid, context= request.cr, request.uid, request.context
        values = {}
        context.update({'record':post.get('token')})
        merge_login_obj = request.registry['merge.user.for.login']
        result = merge_login_obj.execute_merge(cr, uid, False, context)
        uid = SUPERUSER_ID
        merge_ids = merge_login_obj.search(cr, uid, [('access_token', '=', post.get('token'))],
                                           context=context)
        if merge_ids:
            merge_brw = merge_login_obj.browse(cr, uid, merge_ids[0], context=context)
            values['main_name'] = merge_brw.user_id.name
            names = []
            auth = []
            for users in merge_brw.user_ids:
                names.append(users.user_id.email)
                auth.append(users.authorized)
            values['users'] = names
            values['auth'] = all(auth)
            values['process'] = 'error'
            values['message'] = 'Error'
        
        return result and \
                 request.website.render("auth_multi.auth_multi_proccess_completed", values) or \
                 request.website.render("auth_multi.auth_multi_token_used", values)
