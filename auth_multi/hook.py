# -*- coding: utf-8 -*-

from openerp import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    # Using default cursor don't find rows in database.
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        env['merge.user.for.login'].change_gmail_fields()
