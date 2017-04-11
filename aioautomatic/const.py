"""Constants used by aioautomatic."""

AUTH_URL = 'https://accounts.automatic.com/oauth/access_token'

DEFAULT_SCOPE = 'scope:location scope:vehicle:profile ' \
                'scope:user:profile scope:trip'
FULL_SCOPE = ' '.join((DEFAULT_SCOPE, 'scope:current_location'))
