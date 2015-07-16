from openerp.osv import osv, fields


class auth_oauth_provider(osv.osv):
    """"""

    _inherit = 'auth.oauth.provider'

    _columns = {
        'url_get_token': fields.char('URL to get Token',
                                     help='URL used to get the user'
                                     ' token in github'),
    }
