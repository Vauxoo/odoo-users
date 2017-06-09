# -*- coding: utf-8 -*-
from __future__ import division
import urlparse
import base64
import werkzeug.urls
import requests
from odoo import models, api, fields, _
from odoo.exceptions import AccessDenied


class ResPartner(models.Model):
    _inherit = 'res.partner'

    uber_driver = fields.Boolean(
        help="Used to identify if the user is an Uber Driver")

    rating = fields.Float('Uber Rating',
                          help="The driver's average rating from "
                          "passengers. New drivers will start with "
                          "a perfect rating of 5.")

    trip_ids = fields.One2many('uber.trips', 'driver_id', 'Trips')

    @api.multi
    def get_trip_information(self):
        """Get the trips history of a driver"""
        for rec in self:
            rec.user_ids.get_driver_trips()

    @api.multi
    def go_trips_view(self):
        self.ensure_one()
        domain = [
            ('driver_id', '=', self.id)]
        return {
            'name': _('Uber Trips'),
            'domain': domain,
            'res_model': 'uber.trips',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form,graph,pivot',
            'view_type': 'form',
            'limit': 80,
        }


class ResUsers(models.Model):

    _inherit = 'res.users'

    @api.model
    def auth_oauth(self, provider, params):
        """Modified to set the id of the user returned by uber api"""
        access_token = params.get('access_token')
        validation = self._auth_oauth_validate(provider, access_token)
        if validation.get('driver_id'):
            # Workaround: uber does not send 'user_id' in Open Graph Api
            validation['user_id'] = validation['driver_id']
        else:
            return super(ResUsers, self).auth_oauth(provider, params)

        # retrieve and sign in user
        login = self._auth_oauth_signin(provider, validation, params)
        if not login:
            raise AccessDenied()
        # return user credentials
        return (self.env.cr.dbname, login, access_token)

    @api.model
    def _generate_signup_values(self, provider, validation, params):
        """Modified to add the values returned by uber api"""
        res = super(ResUsers, self)._generate_signup_values(provider,
                                                            validation, params)
        if (validation.get('picture') and
                urlparse.urlparse(validation.get('picture')).scheme):
            res.update(
                {'image': base64.b64encode(
                    requests.get(validation.get('picture')).content)})
        name = '%(first_name)s %(last_name)s' % validation
        res.update(
            {'phone': validation.get('phone_number'),
             'name': name.strip() or res.get('email'),
             'uber_driver': True,
             'rating': validation.get('rating')})
        return res

    @api.multi
    def get_dict_trips_values(self, trip):
        """Get the values needed to created the trips made by a drivers
        :param trip:  Details of the trip made
        :type trip: dict

        :return: Values to create a record on uber.trip object
        :rtype: dict
        """
        val = {
            'driver_id': self.partner_id.id,
            'trip': trip.get('trip_id'),
            'vehicle': trip.get('vehicle_id'),
            'pickup':  (trip.get('pickup', {}).get('timestamp')
                        if trip.get('pickup') else False),
            'drop_off': (trip.get('dropoff', {}).get('timestamp')
                         if trip.get('dropoff') else False),
            'distance': trip.get('distance'),
            'duration': (trip.get('duration', 0) / 60.0),
            'status': trip.get('status'),
            'start_city': trip.get('start_city').get('display_name'),
            'start_latitude': trip.get('start_city').get('latitude'),
            'start_longitude': trip.get('start_city').get('longitude'),
            'fare': trip.get('fare'),
            'trip_status_ids': [
                (0, 0, {'status': i.get('status'),
                        'time': i.get('timestamp')})
                for i in trip.get('status_changes')]
        }
        return val

    @api.multi
    def get_driver_trips(self):
        """Get the trips history of a driver"""
        uber = self.env['uber.trips']
        for rec in self:
            prov = self.env.ref('uber_oauth.provider_uber')
            if not prov == rec.oauth_provider_id:
                return  # Add a raise here
            url = 'https://api.uber.com/v1/partners/trips'
            params = werkzeug.url_encode(
                {'access_token': rec.oauth_access_token,
                 'limit': 50})
            info = requests.get(url + '?' + params)
            info = info.json()
            if info.get('count') > 50:
                loops = int(info.get('count') / 50) + 1
                for loop in range(loops):
                    for trip in info.get('trips', []):
                        val = rec.get_dict_trips_values(trip)
                        if not uber.search_count(
                            [('trip', '=', val.get('trip')),
                             ('driver_id', '=', rec.partner_id.id)]):
                            uber.sudo().create(val)
                    last_trip = (val.get('trip_status_ids', 0) and
                                 val.get('trip_status_ids',
                                         loop)[0][2].get('time'))
                    params = werkzeug.url_encode(
                        {'access_token': rec.oauth_access_token,
                         'limit': 50,
                         'to_time': last_trip})
                    info = requests.get(url + '?' + params)
                    info = info.json()
            else:
                for trip in info.get('trips', []):
                    val = rec.get_dict_trips_values(trip)
                    if not uber.search_count(
                        [('trip', '=', val.get('trip')),
                         ('driver_id', '=', rec.partner_id.id)]):
                        uber.sudo().create(val)
        return True
