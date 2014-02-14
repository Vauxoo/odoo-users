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
        url = '?db=%s&login=%s&record=%s#action=%s' % (db, kw.get('login'),
                                                       kw.get('record'),
                                                       kw.get('action'))
        req.context.update({'prueba':'otra'})
        path = req.httprequest.url.split('/do_merge')
        return set_cookie_and_redirect(req, url)

    @openerpweb.httprequest
    def apply_merge(self, req, server_action=None, db=None, **kw):
        print 30*'algooooooooo'
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
