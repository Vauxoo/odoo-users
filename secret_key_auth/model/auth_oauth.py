# -*- coding: utf-8 -*-
from openerp import models, fields


class AuthOauthProvider(models.Model):

    _inherit = 'auth.oauth.provider'

    client_secret = fields.Char('Client Secret',
                                help='The client secret you received')
