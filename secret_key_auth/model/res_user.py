# -*- coding: utf-8 -*-
import logging
from openerp import models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _auth_oauth_rpc(self, cr, uid, endpoint, access_token, context=None):
        context = context or {}
        response = super(ResUsers, self)._auth_oauth_rpc(cr, uid, endpoint,
                                                         access_token,
                                                         context=context)
        if not response.get('user_id', False):
            response.update({
                'user_id': response.get('id'),
            })
        return response
