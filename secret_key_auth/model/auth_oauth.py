# -*- coding: utf-8 -*-
from odoo import models, fields


class AuthOauthProvider(models.Model):

    _inherit = 'auth.oauth.provider'

    client_secret = fields.Char(help='The client secret you received')

    url_get_token = fields.Char('URL to get Token',
                                help='URL used to get the user'
                                ' token')
