"""API Response validation."""
from datetime import datetime

import voluptuous as vol


def timestamp(value):
    """Check that input is a datetime and return the timestamp."""
    if not isinstance(value, datetime):
        raise vol.Invalid("Timestamp must be a datetime object.")

    return value.timestamp()

def opt(key):
    """Create an optional key that returns a default of None."""
    return vol.Optional(key, default=None)

opt_str = vol.Any(str, None)
opt_int = vol.Any(int, None)
opt_float = vol.Any(float, None)
opt_datetime = vol.Any(vol.Datetime(), None)


_REQUEST_BASE = vol.Schema({}, required=False)

VEHICLES_REQUEST = _REQUEST_BASE.extend({
    "created_at__lte": timestamp,
    "created_at__gte": timestamp,
    "updated_at__lte": timestamp,
    "updated_at__gte": timestamp,
    "vin": str,
    "page": vol.All(int, vol.Range(min=1)),
    "limit": vol.All(int, vol.Range(min=1, max=250)),
})

TRIPS_REQUEST = _REQUEST_BASE.extend({
    "started_at__lte": timestamp,
    "started_at__gte": timestamp,
    "ended_at__lte": timestamp,
    "ended_at__gte": timestamp,
    "vehicle": str,
    "tags__in": str,
    "page": vol.All(int, vol.Range(min=1)),
    "limit": vol.All(int, vol.Range(min=1, max=250)),
})

_RESPONSE_BASE = vol.Schema({}, required=True, extra=vol.REMOVE_EXTRA)

AUTH_TOKEN = _RESPONSE_BASE.extend({
    "access_token": str,
    "expires_in": int,
    "scope": str,
    "refresh_token": str,
    "token_type": vol.In(["Bearer"]),
})

LIST_METADATA = _RESPONSE_BASE.extend({
    "count": vol.All(int, vol.Range(min=0)),
    "next": opt_str,
    "previous": opt_str,
})

LIST_RESPONSE = _RESPONSE_BASE.extend({
    "_metadata": LIST_METADATA,
    "results": [],
})

VEHICLE = _RESPONSE_BASE.extend({
    "url": str,
    "id": str,
    opt("vin"): opt_str,
    opt("created_at"): vol.Datetime(),
    opt("updated_at"): vol.Datetime(),
    opt("make"): opt_str,
    opt("model"): opt_str,
    opt("year"): opt_int,
    opt("submodel"): opt_str,
    opt("display_name"): opt_str,
    opt("fuel_grade"): opt_str,
    opt("fuel_level_percent"): vol.Any(
        vol.All(float, vol.Range(min=0, max=100)), None),
    opt("battery_voltage"): vol.Any(vol.All(float, vol.Range(min=0)), None),
})

LOCATION = _RESPONSE_BASE.extend({
    "lat": float,
    "lon": float,
    "accuracy_m": float,
})

ADDRESS = _RESPONSE_BASE.extend({
    opt("name"): opt_str,
    opt("display_name"): opt_str,
    opt("street_number"): opt_str,
    opt("streen_name"): opt_str,
    opt("city"): opt_str,
    opt("state"): opt_str,
    opt("country"): opt_str,
})

VEHICLE_EVENT = _RESPONSE_BASE.extend({
    "type": str,
    opt("lat"): opt_float,
    opt("lon"): opt_float,
    opt("created_at"): vol.Datetime(),
    opt("g_force"): opt_float,
})

TRIP = _RESPONSE_BASE.extend({
    "url": str,
    "id": str,
    "driver": opt_str,
    opt("user"): opt_str,
    opt("started_at"): opt_datetime,
    opt("ended_at"): opt_datetime,
    opt("distance_m"): opt_float,
    opt("duration_s"): opt_float,
    opt("vehicle"): opt_str,
    "start_location": LOCATION,
    "start_address": ADDRESS,
    "end_location": LOCATION,
    "end_address": ADDRESS,
    opt("path"): opt_str,
    opt("fuel_cost_ust"): opt_float,
    opt("fuel_volume_l"): opt_float,
    opt("average_kmpl"): opt_float,
    opt("average_from_epa_kmpl"): opt_float,
    opt("score_events"): opt_float,
    opt("score_speeding"): opt_float,
    opt("hard_brakes"): opt_int,
    opt("hard_accels"): opt_int,
    opt("duration_over_70_s"): opt_int,
    opt("duration_over_75_s"): opt_int,
    opt("duration_over_80_s"): opt_int,
    vol.Optional("vehicle_events", default=[]): [VEHICLE_EVENT],
    opt("start_timezone"): opt_str,
    opt("end_timezone"): opt_str,
    opt("city_fraction"): opt_float,
    opt("highway_fraction"): opt_float,
    opt("night_driving_fraction"): opt_float,
    opt("idling_time_s"): opt_int,
    "tags": [str],
})
