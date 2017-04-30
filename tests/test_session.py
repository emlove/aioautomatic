"""Tests for automatic client."""
from datetime import datetime, timezone
from aioautomatic.session import Session

from unittest.mock import MagicMock, patch
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


def test_session_auto_refresh(aiohttp_session):
    """Test auto-refreshing a session with the refresh token."""
    client = AsyncMock()
    client.client_session = aiohttp_session
    client.request_kwargs = {}
    data = {
        "access_token": "123",
        "refresh_token": "ABCD",
        "expires_in": 12345,
        "scope": ("scope:location scope:vehicle:profile "
                  "scope:user:profile scope:trip"),
    }

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

    with patch.object(aiohttp_session.loop, 'call_at') as mock_call_at:
        session = Session(client, **data)
        assert mock_call_at.called
        assert len(mock_call_at.mock_calls) == 1

    with patch.object(aiohttp_session.loop, 'create_task'):
        with patch.object(session, 'refresh') as mock_refresh:
            assert not mock_refresh.called
            mock_call_at.mock_calls[0][1][1]()
            assert mock_refresh.called
            assert len(mock_refresh.mock_calls) == 1


def test_get_vehicles(session):
    """Test getting vehicle list."""
    resp = AsyncMock()
    resp.status = 200
    resp.json.return_value = {
        "_metadata": {
            "count": 1,
            "next": None,
            "previous": None,
            },
        "results": [{
            "url": "mock_url",
            "id": "mock_id",
            "make": "mock_make",
            "model": "mock_model",
            "submodel": None,
            "created_at": "2015-03-20T01:43:36.738000Z",
            "fuel_level_percent": 73.9,
            }],
    }
    session._client_session.request.return_value = resp

    dt = datetime(2017, 1, 28)
    vehicle = session.loop.run_until_complete(
        session.get_vehicles(vin="VINVIN", created_at__gte=dt))[0]
    assert session._client_session.request.called
    assert len(session._client_session.request.mock_calls) == 2
    assert session._client_session.request.mock_calls[0][1][0] == "GET"
    assert session._client_session.request.mock_calls[0][1][1][:34] == \
        "https://api.automatic.com/vehicle?"
    assert vehicle.url == "mock_url"
    assert vehicle.id == "mock_id"
    assert vehicle.make == "mock_make"
    assert vehicle.model == "mock_model"
    assert vehicle.vin is None
    assert vehicle.submodel is None
    assert vehicle.created_at == datetime(
        2015, 3, 20, 1, 43, 36, 738000, tzinfo=timezone.utc)
    assert vehicle.fuel_level_percent == 73.9


def test_get_trips(session):
    """Test getting trip list."""
    resp = AsyncMock()
    resp.status = 200
    resp.json.return_value = {
        "_metadata": {
            "count": 1,
            "next": None,
            "previous": None,
            },
        "results": [{
            "url": "mock_url",
            "id": "mock_id",
            "driver": "mock_driver",
            "user": "mock_user",
            "start_location": {
                "lat": 43.12345,
                "lon": 34.54321,
                "accuracy_m": 12.2,
                },
            "end_location": {
                "lat": 53.12345,
                "lon": 44.54321,
                "accuracy_m": 11.2,
                },
            "start_address": {
                "name": "123 Fake St",
                },
            "end_address": {
                "name": "456 Elm",
                },
            "hard_brakes": 2,
            "path": None,
            "started_at": "2015-03-21T01:43:36.738000Z",
            "ended_at": "2015-03-21T04:45:36.738000Z",
            "tags": ["business"],
            }],
    }
    session._client_session.request.return_value = resp

    dt = datetime(2017, 1, 28)
    trip = session.loop.run_until_complete(
        session.get_trips(vehicle="vehicle_id", started_at__gte=dt))[0]
    assert session._client_session.request.called
    assert len(session._client_session.request.mock_calls) == 2
    assert session._client_session.request.mock_calls[0][1][0] == "GET"
    assert session._client_session.request.mock_calls[0][1][1][:31] == \
        "https://api.automatic.com/trip?"
    assert trip.url == "mock_url"
    assert trip.id == "mock_id"
    assert trip.driver == "mock_driver"
    assert trip.user == "mock_user"
    assert trip.fuel_cost_usd is None
    assert trip.start_location.lat == 43.12345
    assert trip.start_location.lon == 34.54321
    assert trip.start_location.accuracy_m == 12.2
    assert trip.end_location.lat == 53.12345
    assert trip.end_location.lon == 44.54321
    assert trip.end_location.accuracy_m == 11.2
    assert trip.start_address.name == "123 Fake St"
    assert trip.start_address.display_name is None
    assert trip.end_address.name == "456 Elm"
    assert trip.end_address.display_name is None
    assert trip.hard_brakes == 2
    assert trip.path is None
    assert trip.started_at == datetime(
        2015, 3, 21, 1, 43, 36, 738000, tzinfo=timezone.utc)
    assert trip.ended_at == datetime(
        2015, 3, 21, 4, 45, 36, 738000, tzinfo=timezone.utc)
    assert trip.tags == ["business"]


def test_get_devices(session):
    """Test getting device list."""
    resp = AsyncMock()
    resp.status = 200
    resp.json.return_value = {
        "_metadata": {
            "count": 1,
            "next": None,
            "previous": None,
            },
        "results": [{
            "url": "mock_url",
            "id": "mock_id",
            "version": 2,
            }],
    }
    session._client_session.request.return_value = resp

    device = session.loop.run_until_complete(session.get_devices())[0]
    assert session._client_session.request.called
    assert len(session._client_session.request.mock_calls) == 2
    assert session._client_session.request.mock_calls[0][1][0] == "GET"
    assert session._client_session.request.mock_calls[0][1][1] == \
        "https://api.automatic.com/device?"
    assert device.url == "mock_url"
    assert device.id == "mock_id"
    assert device.version == 2


def test_get_user(session):
    """Test getting user information."""
    resp = AsyncMock()
    resp.status = 200
    resp.json.return_value = {
        "url": "mock_url",
        "id": "mock_id",
        "username": "mock_username",
        "first_name": "mock_firstname",
        "email": "mock_email@example.com",
    }
    session._client_session.request.return_value = resp

    user = session.loop.run_until_complete(session.get_user())
    assert session._client_session.request.called
    assert len(session._client_session.request.mock_calls) == 2
    assert session._client_session.request.mock_calls[0][1][0] == "GET"
    assert session._client_session.request.mock_calls[0][1][1] == \
        "https://api.automatic.com/user/me"
    assert user.url == "mock_url"
    assert user.id == "mock_id"
    assert user.username == "mock_username"
    assert user.first_name == "mock_firstname"
    assert user.last_name is None
    assert user.email == "mock_email@example.com"

    session._client_session.request.reset_mock()
    resp.json.return_value = {
        "url": "mock_profile_url",
        "user": "mock_user",
        "date_joined": "2015-03-20T01:43:36.738000Z",
    }
    profile = session.loop.run_until_complete(user.get_profile())
    assert session._client_session.request.called
    assert len(session._client_session.request.mock_calls) == 2
    assert session._client_session.request.mock_calls[0][1][0] == "GET"
    assert session._client_session.request.mock_calls[0][1][1] == \
        "https://api.automatic.com/user/mock_id/profile"
    assert profile.url == "mock_profile_url"
    assert profile.user == "mock_user"
    assert profile.date_joined == datetime(
        2015, 3, 20, 1, 43, 36, 738000, tzinfo=timezone.utc)

    session._client_session.request.reset_mock()
    resp.json.return_value = {
        "url": "mock_metadata_url",
        "user": "mock_user",
        "firmware_version": "1.2.3.4",
        "is_app_latest_version": False,
        "is_staff": True,
    }
    metadata = session.loop.run_until_complete(user.get_metadata())
    assert session._client_session.request.called
    assert len(session._client_session.request.mock_calls) == 2
    assert session._client_session.request.mock_calls[0][1][0] == "GET"
    assert session._client_session.request.mock_calls[0][1][1] == \
        "https://api.automatic.com/user/mock_id/metadata"
    assert metadata.url == "mock_metadata_url"
    assert metadata.user == "mock_user"
    assert metadata.firmware_version == "1.2.3.4"
    assert metadata.app_version is None
    assert metadata.is_app_latest_version is False
    assert metadata.is_staff is True


def test_get_trip(session):
    """Test getting trip information."""
    resp = AsyncMock()
    resp.status = 200
    resp.json.return_value = {
        "url": "mock_url",
        "id": "mock_id",
        "start_location": {
            "lat": 43.12345,
            "lon": 34.54321,
            "accuracy_m": 12.2,
            },
        "end_location": {
            "lat": 53.12345,
            "lon": 44.54321,
            "accuracy_m": 11.2,
            },
        "start_address": {
            "name": "123 Fake St",
            },
        "end_address": {
            "name": "456 Elm",
            },
    }
    session._client_session.request.return_value = resp

    trip = session.loop.run_until_complete(session.get_trip("mock_id"))
    assert session._client_session.request.called
    assert len(session._client_session.request.mock_calls) == 2
    assert session._client_session.request.mock_calls[0][1][0] == "GET"
    assert session._client_session.request.mock_calls[0][1][1] == \
        "https://api.automatic.com/trip/mock_id"
    assert trip.url == "mock_url"
    assert trip.id == "mock_id"
    assert trip.start_location.lat == 43.12345
    assert trip.start_location.lon == 34.54321


def test_get_vehicle(session):
    """Test getting vehicle information."""
    resp = AsyncMock()
    resp.status = 200
    resp.json.return_value = {
        "url": "mock_url",
        "id": "mock_id",
        "display_name": "Geo Metro",
    }
    session._client_session.request.return_value = resp

    vehicle = session.loop.run_until_complete(session.get_vehicle("mock_id"))
    assert session._client_session.request.called
    assert len(session._client_session.request.mock_calls) == 2
    assert session._client_session.request.mock_calls[0][1][0] == "GET"
    assert session._client_session.request.mock_calls[0][1][1] == \
        "https://api.automatic.com/vehicle/mock_id"
    assert vehicle.url == "mock_url"
    assert vehicle.id == "mock_id"
    assert vehicle.display_name == "Geo Metro"


def test_get_device(session):
    """Test getting device information."""
    resp = AsyncMock()
    resp.status = 200
    resp.json.return_value = {
        "url": "mock_url",
        "id": "mock_id",
        "version": 2,
    }
    session._client_session.request.return_value = resp

    device = session.loop.run_until_complete(session.get_device("mock_id"))
    assert session._client_session.request.called
    assert len(session._client_session.request.mock_calls) == 2
    assert session._client_session.request.mock_calls[0][1][0] == "GET"
    assert session._client_session.request.mock_calls[0][1][1] == \
        "https://api.automatic.com/device/mock_id"
    assert device.url == "mock_url"
    assert device.id == "mock_id"
    assert device.version == 2
