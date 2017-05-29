# -*- coding: utf-8 -*-
import logging
import urlparse
import werkzeug.utils
import requests
import simplejson
from odoo import http, api, SUPERUSER_ID
from odoo import registry as registry_get
from odoo.http import request
from odoo.addons.auth_oauth.controllers.main import (OAuthController,
                                                     OAuthLogin,
                                                     fragment_to_query_string)


_logger = logging.getLogger(__name__)


class OAuthLoginInherit(OAuthLogin):
    def list_providers(self):
        res = super(OAuthLoginInherit, self).list_providers()
        try:
            uber = request.env.ref('uber_oauth.provider_uber').sudo()
            for provider in uber and res:
                if uber.validation_endpoint == provider.get(
                        'validation_endpoint'):
                    provider['auth_link'] = provider.get('auth_link').replace(
                        'http%', 'https%').replace('token', 'code')
        except BaseException:
            return res
        return res


class OAuthControllerInherit(OAuthController):

    @http.route('/auth_oauth/signin', type='http', auth='none')
    @fragment_to_query_string
    def signin(self, **kw):
        state = simplejson.loads(kw['state'])
        dbname = state['d']
        provider = state['p']
        registry = registry_get(dbname)
        context = state.get('c', {})
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, context)
            redirect = env.ref('uber_oauth.default_uber_oauth_redirect_config')
            uber = env.ref('uber_oauth.provider_uber')
            if (not kw.get('access_token') and kw.get('code') and
                    uber.id == provider):
                p_brw = env['auth.oauth.provider'].\
                    browse(provider)
                params = werkzeug.url_encode({
                    'code': kw.get('code'),
                    'client_id': p_brw.client_id,
                    'redirect_uri': redirect.value,
                    'grant_type': 'authorization_code',
                    'scope': p_brw.scope,
                    'client_secret': p_brw.client_secret})
                endpoint = p_brw.url_get_token
                if endpoint:
                    if urlparse.urlparse(endpoint)[4]:
                        url = endpoint + '&' + params
                    else:
                        url = endpoint + '?' + params
                    furl = requests.post(url)
                    response = furl.json() if furl.status_code == 200 else {}
                    kw.pop('code', '')
                    kw.update({'access_token': response.get('access_token')})
        return super(OAuthControllerInherit, self).signin(**kw)
