from openerp.osv import osv, fields

class auth_oauth_provider(osv.osv):
    """"""

    _inherit = 'auth.oauth.provider'

    _columns = {
        'client_secret' : fields.char('Client Secret', help='The client secret you received'),
        'url_get_token' : fields.char('URL to get Token', help='URL used to get the user token in github'),
    }
