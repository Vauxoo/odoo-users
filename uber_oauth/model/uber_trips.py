# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, api, fields


class UberTripsStatus(models.Model):

    _name = 'uber.trips.status'

    @api.depends('time')
    def _compute_date(self):
        """Change the timestamp to a readable format"""
        for rec in self:
            value = datetime.fromtimestamp(rec.time)
            rec.date = value.strftime('%Y-%m-%d %H:%M:%S') if rec.time else ''

    trip_id = fields.Many2one('uber.trips', 'Trip', index=True)

    time = fields.Integer(help="Unix timestamp of the trip's status change.")

    date = fields.Datetime(compute='_compute_date', store=True,
                           help="Date of the trip's status change.")

    status = fields.Char(help="Status the trip changed to. Can be accepted,"
                         " driver_arrived, trip_began, completed, "
                         "driver_canceled, rider_canceled.")


class UberTrips(models.Model):

    _name = 'uber.trips'

    @api.depends('drop_off', 'pickup')
    def _compute_date(self):
        """Change the timestamp to a readable format"""
        for rec in self:
            val = datetime.fromtimestamp(rec.pickup)
            rec.pickup_date = val.strftime(
                '%Y-%m-%d %H:%M:%S') if rec.pickup else ''

            val = datetime.fromtimestamp(rec.drop_off)
            rec.drop_off_date = val.strftime(
                '%Y-%m-%d %H:%M:%S') if rec.drop_off else ''

    driver_id = fields.Many2one('res.partner', 'Driver', index=True)

    trip = fields.Char(help="Unique identifier of the trip.", index=True)

    vehicle = fields.Char(help="Unique identifier of the trip's vehicle.")

    pickup = fields.Integer(help="Unix timestamp of the trip's pickup "
                            "time. Can be empty for canceled trips")

    pickup_date = fields.Datetime(
        compute="_compute_date", store=True,
        help="Date of the trip's pickup "
        "time. Can be empty for canceled trips")

    drop_off = fields.Integer(help="Unix timestamp of the trip's drop off "
                              "time. Can be null for canceled trips.")

    drop_off_date = fields.Datetime(
        compute="_compute_date", store=True,
        help="Date of the trip's drop off "
        "time. Can be null for canceled trips.")

    distance = fields.Float(help="Trip's distance (in miles). "
                            "Can be empty for canceled trips.")

    duration = fields.Float(help="Trip's duration (in minutes).")

    status = fields.Char(help="Trip's most recent status. "
                         "Can be rider_canceled, driver_canceled, completed.")

    start_city = fields.Char(help="Display name for trip's starting city.")

    start_latitude = fields.Float(
        'Latitude', help="Latitude for trip's starting city.")

    start_longitude = fields.Float(
        'Longitude', help="Longitude for trip's starting city.")

    fare = fields.Float(help="Trip's Fare")

    trip_status_ids = fields.One2many('uber.trips.status', 'trip_id',
                                      "Trips Status")
