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


DATETIME_FORMAT_MS = '%Y-%m-%dT%H:%M:%S.%fZ%z'
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ%z'


def coerce_datetime(value):
    """Coerce a value to datetime."""
    if isinstance(value, datetime):
        return value

    value = '{}+0000'.format(value)
    try:
        return datetime.strptime(value, DATETIME_FORMAT_MS)
    except (TypeError, ValueError):
        try:
            return datetime.strptime(value, DATETIME_FORMAT)
        except (TypeError, ValueError):
            raise vol.DatetimeInvalid(
                'Value {} does not match expected format {}'.format(
                    value, DATETIME_FORMAT))


OPT_BOOL = vol.Any(bool, None)
OPT_DATETIME = vol.Any(coerce_datetime, None)
OPT_FLOAT = vol.Any(vol.Coerce(float), None)
OPT_INT = vol.Any(int, None)
OPT_STR = vol.Any(str, None)


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

DEVICES_REQUEST = _REQUEST_BASE.extend({
    "device__serial_number": str,
    "page": vol.All(int, vol.Range(min=1)),
    "limit": vol.All(int, vol.Range(min=1, max=250)),
})

USER_REQUEST = _REQUEST_BASE.extend({
    "id": str,
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
    "next": OPT_STR,
    "previous": OPT_STR,
})

LIST_RESPONSE = _RESPONSE_BASE.extend({
    "_metadata": LIST_METADATA,
    "results": [lambda _: _],  # Results are validated independently
})

VEHICLE_DTCS = _RESPONSE_BASE.extend({
    opt("code"): OPT_STR,
    opt("description"): OPT_STR,
    opt("created_at"): OPT_DATETIME,
})

LOCATION = _RESPONSE_BASE.extend({
    "lat": vol.Coerce(float),
    "lon": vol.Coerce(float),
    "accuracy_m": vol.Coerce(float),
})

REALTIME_LOCATION = LOCATION.extend({
    opt("created_at"): OPT_DATETIME,
})

VEHICLE = _RESPONSE_BASE.extend({
    "url": str,
    "id": str,
    opt("vin"): OPT_STR,
    opt("created_at"): OPT_DATETIME,
    opt("updated_at"): OPT_DATETIME,
    opt("make"): OPT_STR,
    opt("model"): OPT_STR,
    opt("year"): OPT_INT,
    opt("submodel"): OPT_STR,
    opt("display_name"): OPT_STR,
    opt("fuel_grade"): OPT_STR,
    opt("fuel_level_percent"): vol.Any(vol.Coerce(float), None),
    opt("battery_voltage"): vol.Any(vol.Coerce(float), None),
    opt("active_dtcs"): vol.Any([VEHICLE_DTCS], None),
    opt("latest_location"): vol.Any(REALTIME_LOCATION, None),
})

ADDRESS = _RESPONSE_BASE.extend({
    opt("name"): OPT_STR,
    opt("display_name"): OPT_STR,
    opt("street_number"): OPT_STR,
    opt("streen_name"): OPT_STR,
    opt("city"): OPT_STR,
    opt("state"): OPT_STR,
    opt("country"): OPT_STR,
})

VEHICLE_EVENT = _RESPONSE_BASE.extend({
    "type": str,
    opt("lat"): OPT_FLOAT,
    opt("lon"): OPT_FLOAT,
    opt("created_at"): coerce_datetime,
    opt("g_force"): OPT_FLOAT,
})

TRIP = _RESPONSE_BASE.extend({
    "url": str,
    "id": str,
    opt("driver"): OPT_STR,
    opt("user"): OPT_STR,
    opt("started_at"): OPT_DATETIME,
    opt("ended_at"): OPT_DATETIME,
    opt("distance_m"): OPT_FLOAT,
    opt("duration_s"): OPT_FLOAT,
    opt("vehicle"): OPT_STR,
    "start_location": LOCATION,
    "start_address": ADDRESS,
    "end_location": LOCATION,
    "end_address": ADDRESS,
    opt("path"): OPT_STR,
    opt("fuel_cost_usd"): OPT_FLOAT,
    opt("fuel_volume_l"): OPT_FLOAT,
    opt("average_kmpl"): OPT_FLOAT,
    opt("average_from_epa_kmpl"): OPT_FLOAT,
    opt("score_events"): OPT_FLOAT,
    opt("score_speeding"): OPT_FLOAT,
    opt("hard_brakes"): OPT_INT,
    opt("hard_accels"): OPT_INT,
    opt("duration_over_70_s"): OPT_INT,
    opt("duration_over_75_s"): OPT_INT,
    opt("duration_over_80_s"): OPT_INT,
    vol.Optional("vehicle_events", default=[]): [VEHICLE_EVENT],
    opt("start_timezone"): OPT_STR,
    opt("end_timezone"): OPT_STR,
    opt("city_fraction"): OPT_FLOAT,
    opt("highway_fraction"): OPT_FLOAT,
    opt("night_driving_fraction"): OPT_FLOAT,
    opt("idling_time_s"): OPT_FLOAT,
    opt("tags"): vol.Any([str], None),
})

DEVICE = _RESPONSE_BASE.extend({
    "id": str,
    opt("url"): OPT_STR,
    opt("version"): OPT_INT,
    opt("direct_access_token"): OPT_STR,
    opt("app_encryption_key"): OPT_STR,
})

USER = _RESPONSE_BASE.extend({
    "url": str,
    "id": str,
    opt("username"): OPT_STR,
    opt("first_name"): OPT_STR,
    opt("last_name"): OPT_STR,
    opt("email"): OPT_STR,
})

USER_PROFILE = _RESPONSE_BASE.extend({
    "url": str,
    opt("user"): OPT_STR,
    opt("date_joined"): OPT_DATETIME,
    # Tagged locations: No API reference documentation?
})

USER_METADATA = _RESPONSE_BASE.extend({
    "url": str,
    opt("user"): OPT_STR,
    opt("firmware_version"): OPT_STR,
    opt("app_version"): OPT_STR,
    opt("os_version"): OPT_STR,
    opt("device_type"): OPT_STR,
    opt("phone_platform"): OPT_STR,
    opt("is_app_latest_version"): OPT_BOOL,
    opt("authenticated_clients"): vol.Any([str], None),
    opt("is_staff"): OPT_BOOL,
})

REALTIME_DEVICE = _RESPONSE_BASE.extend({
    "id": str,
})

REALTIME_BASE = _RESPONSE_BASE.extend({
    "id": str,
    "user": USER,
    "type": vol.In([
        "trip:finished",
        "ignition:on",
        "ignition:off",
        "notification:speeding",
        "notification:hard_brake",
        "notification:hard_accel",
        "mil:on",
        "mil:off",
        "location:updated",
        "vehicle:status_report",
        ]),
    opt("created_at"): OPT_DATETIME,
    opt("time_zone"): OPT_STR,
    opt("location"): vol.Any(REALTIME_LOCATION, None),
    "vehicle": VEHICLE,
    "device": DEVICE,
})

REALTIME_TRIP_FINISHED = REALTIME_BASE.extend({
    "trip": TRIP,
})

REALTIME_SPEEDING = REALTIME_BASE.extend({
    "velocity_kph": vol.Coerce(float),
})

REALTIME_HARD_BRAKE = REALTIME_BASE.extend({
    "g_force": vol.Coerce(float),
})

REALTIME_MIL_ON = REALTIME_BASE.extend({
    "dtcs": [VEHICLE_DTCS],
})

REALTIME_MIL_OFF = REALTIME_MIL_ON.extend({
    "user_cleared": bool,
})

REALTIME_HARD_ACCEL = REALTIME_BASE.extend({
    "g_force": vol.Coerce(float),
})
