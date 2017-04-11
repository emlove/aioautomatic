"""API Response validation."""
import voluptuous as vol

_BASE = vol.Schema({}, required=True, extra=vol.REMOVE_EXTRA)

AUTH_TOKEN = _BASE.extend({
    "access_token": str,
    "expires_in": int,
    "scope": str,
    "refresh_token": str,
    "token_type": vol.In(["Bearer"]),
})
