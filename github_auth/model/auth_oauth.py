# coding: utf-8
from openerp import models, fields


class AuthOauthProvider(models.Model):

    _inherit = 'auth.oauth.provider'

    url_get_token = fields.Char('URL to get Token',
                                help='URL used to get the user'
                                ' token in github')
