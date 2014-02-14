from openerp.addons.web import http                                                                    
from openerp.addons.web.http import request
import openerp.addons.web.controllers.main as webmain
import openerp
from openerp import SUPERUSER_ID

from urllib import quote_plus

openerpweb = http


#----------------------------------------------------------
# Controller
#----------------------------------------------------------
class auth_muti_login(openerpweb.Controller):

    @http.route(['/do_merge/execute_merge'], type='http', auth="user", website=True, multilang=True)
    def execute_merge(self, **post):
        print 'post', post
        url = '?db=%s&login=%s&record=%s#action=%s' % ('saas', post.get('login'),
                                                       post.get('record'),
                                                       post.get('action'))
        query = {'redirect': u'/'}
        return http.local_redirect('/web/login', query=query)

    @http.route(['/do_merge/apply_merge'], type='http', auth="user", website=True, multilang=True)
    def apply_merge(self, req, server_action=None, db=None, **kw):
        dbname = db
        context = {}
        context.update(kw)
        registry = RegistryManager.get(dbname)
        with registry.cursor() as cr:
            u = registry.get('merge.user.for.login')
            credentials = u.execute_merge(cr, SUPERUSER_ID, [1], context)
            cr.commit()
        #return set_cookie_and_redirect(req, url)
        return 'WTF'
