# -*- coding: utf-8 -*-
import functools
import urllib2
import logging
import simplejson
import urlparse
import werkzeug.utils

from openerp import SUPERUSER_ID
from openerp import http
from openerp.addons.auth_oauth.controllers.main import OAuthController
from openerp.modules.registry import RegistryManager

_logger = logging.getLogger(__name__)


def fragment_to_query_string(func):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        if not kw:
            return """<html><head><script>
                var l = window.location;
                var q = l.hash.substring(1);
                var r = l.pathname + l.search;
                if(q.length !== 0) {
                    var s = l.search ? (l.search === '?' ? '' : '&') : '?';
                    r = l.pathname + l.search + s + q;
                }
                if (r == l.pathname) {
                    r = '/';
                }
                window.location = r;
            </script></head><body></body></html>"""
        return func(self, *a, **kw)
    return wrapper


class OAuthControllerInherit(OAuthController):

    @http.route('/auth_oauth/signin', type='http', auth='none')
    @fragment_to_query_string
    def signin(self, **kw):
        state = simplejson.loads(kw['state'])
        dbname = state['d']
        provider = state['p']
        registry = RegistryManager.get(dbname)
        with registry.cursor() as cr:
            if not kw.get('access_token') and kw.get('code'):
                p_brw = registry.get('auth.oauth.provider').\
                    browse(cr, SUPERUSER_ID, provider)
                params = werkzeug.url_encode({
                    'code': kw.get('code'),
                    'client_id': p_brw.client_id,
                    'client_secret': p_brw.client_secret})
                endpoint = p_brw.url_get_token
                if endpoint:
                    if urlparse.urlparse(endpoint)[4]:
                        url = endpoint + '&' + params
                    else:
                        url = endpoint + '?' + params
                    furl = urllib2.urlopen(url)
                    response = furl.read()
                    response = werkzeug.url_decode(response)
                    kw.update({'access_token': response.get('access_token')})
        return super(OAuthControllerInherit, self).signin(**kw)
