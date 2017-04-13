"""Tests for automatic client."""
from unittest.mock import MagicMock
from tests.common import AsyncMock


def test_session_refresh(session):
    """Test refreshing a session with the refresh token."""
    resp = AsyncMock()
    resp.status = 200
    resp.json.return_value = {
        "access_token": "mock_access",
        "expires_in": 123456,
        "scope": ("scope:location scope:vehicle:profile "
                  "scope:user:profile scope:trip"),
        "refresh_token": "mock_refresh",
        "token_type": "Bearer",
    }
    session._client_session.request.return_value = resp
    refresh_token = session._refresh_token
    renew_handle = MagicMock()
    session._renew_handle = renew_handle
    session._client.client_id = "123"
    session._client.client_secret = "456"

    session.loop.run_until_complete(session.refresh())
    assert session._client_session.request.called
    assert len(session._client_session.request.mock_calls) == 2
    assert session._client_session.request.mock_calls[0][1][0] == "POST"
    assert session._client_session.request.mock_calls[0][1][1] == \
        "https://accounts.automatic.com/oauth/access_token"
    assert session._client_session.request.mock_calls[0][2]['data'] == {
        "client_id": "123",
        "client_secret": "456",
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    assert renew_handle.cancel.called
