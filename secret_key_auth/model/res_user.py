# -*- coding: utf-8 -*-
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _auth_oauth_rpc(self, endpoint, access_token):
        response = super(ResUsers, self)._auth_oauth_rpc(endpoint,
                                                         access_token)
        if not response.get('user_id', False):
            response.update({
                'user_id': response.get('id'),
            })
        return response
