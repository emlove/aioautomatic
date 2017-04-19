"""Constants used by aioautomatic."""

AUTH_URL = 'https://accounts.automatic.com/oauth/access_token'
BASE_API_URL = 'https://api.automatic.com'
VEHICLE_URL = '{}/vehicle'.format(BASE_API_URL)
TRIP_URL = '{}/trip'.format(BASE_API_URL)
DEVICE_URL = '{}/device'.format(BASE_API_URL)

DEFAULT_SCOPE = 'scope:location scope:vehicle:profile ' \
                'scope:user:profile scope:trip'
FULL_SCOPE = ' '.join((DEFAULT_SCOPE, 'scope:current_location'))
