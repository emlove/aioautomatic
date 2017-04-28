"""Constants used by aioautomatic."""

AUTH_URL = 'https://accounts.automatic.com/oauth/access_token'
BASE_API_URL = 'https://api.automatic.com'
WEBSOCKET_SESSION_URL = 'https://stream.automatic.com/socket.io/?{}'
WEBSOCKET_URL = 'wss://stream.automatic.com/socket.io/?{}'
DEVICES_URL = '{}/device'.format(BASE_API_URL)
DEVICE_URL = '{}/device/{{}}'.format(BASE_API_URL)
TRIP_URL = '{}/trip'.format(BASE_API_URL)
USER_URL = '{}/user/{{}}'.format(BASE_API_URL)
USER_METADATA_URL = '{}/user/{{}}/metadata'.format(BASE_API_URL)
USER_PROFILE_URL = '{}/user/{{}}/profile'.format(BASE_API_URL)
VEHICLES_URL = '{}/vehicle'.format(BASE_API_URL)
VEHICLE_URL = '{}/vehicle/{{}}'.format(BASE_API_URL)
