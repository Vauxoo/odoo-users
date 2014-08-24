import logging
from openerp.osv import osv

_logger = logging.getLogger(__name__)

class res_users(osv.Model):
    _inherit = 'res.users'

    def _auth_oauth_rpc(self, cr, uid, endpoint, access_token, context=None):
        context = context or {}
        response = super(res_users, self)._auth_oauth_rpc(cr, uid, endpoint, access_token, context=context)
        if not response.get('user_id', False):
            response.update({
                'user_id': response.get('id'),
            })
        return response
