"""Tests for automatic data."""
from aioautomatic import data

from tests.common import AsyncMock


def test_realtime_location(client):
    """Test realtime location."""
    event = data.BaseRealtimeEvent(client, {
        'id': 'mock_id',
        'user': {
            'id': 'mock_user_id',
            'url': 'mock_user_url',
            },
        'type': 'location:updated',
        'vehicle': {
            'id': 'mock_vehicle_id',
            'url': 'mock_vehicle_url',
            },
        'device': {
            'id': 'mock_device_id',
            },
        'location': {
            'lat': 12.3,
            'lon': 23.4,
            'accuracy_m': 34.5,
            },
    })
    assert event.location.lat == 12.3
    assert event.location.lon == 23.4
    assert event.location.accuracy_m == 34.5


def test_realtime_mil_on(client):
    """Test realtime mil on event."""
    event = data.RealtimeMILOn(client, {
        'id': 'mock_id',
        'user': {
            'id': 'mock_user_id',
            'url': 'mock_user_url',
            },
        'type': 'location:updated',
        'vehicle': {
            'id': 'mock_vehicle_id',
            'url': 'mock_vehicle_url',
            },
        'device': {
            'id': 'mock_device_id',
            },
        'dtcs': [
            {
                'code': 'ABC123',
                'description': 'Flux Capacitor Fault'}
            ],
    })
    assert len(event.dtcs) == 1
    assert event.dtcs[0].code == 'ABC123'
    assert event.dtcs[0].description == 'Flux Capacitor Fault'


def test_realtime_get_user(client):
    """Test getting user information."""
    event = data.BaseRealtimeEvent(client, {
        'id': 'mock_id',
        'user': {
            'id': 'mock_user_id',
            'url': 'mock_user_url',
            },
        'type': 'location:updated',
        'vehicle': {
            'id': 'mock_vehicle_id',
            'url': 'mock_vehicle_url',
            },
        'device': {
            'id': 'mock_device_id',
            },
    })
    event._get = AsyncMock()
    resp = {
        'id': 'mock_user_id',
        'url': 'mock_user_url',
        'username': 'mock_username',
    }
    event._get.return_value = resp

    user = client.loop.run_until_complete(event.get_user())

    assert event._get.called
    assert len(event._get.mock_calls) == 1
    assert event._get.mock_calls[0][1][0] == \
        'https://api.automatic.com/user/mock_user_id'
    assert user.id == 'mock_user_id'
    assert user.url == 'mock_user_url'
    assert user.username == 'mock_username'


def test_realtime_get_vehicle(client):
    """Test getting vehicle information."""
    event = data.BaseRealtimeEvent(client, {
        'id': 'mock_id',
        'user': {
            'id': 'mock_user_id',
            'url': 'mock_user_url',
            },
        'type': 'location:updated',
        'vehicle': {
            'id': 'mock_vehicle_id',
            'url': 'mock_vehicle_url',
            },
        'device': {
            'id': 'mock_device_id',
            },
    })
    event._get = AsyncMock()
    resp = {
        'id': 'mock_vehicle_id',
        'url': 'mock_vehicle_url',
        'display_name': 'mock_display_name',
    }
    event._get.return_value = resp

    vehicle = client.loop.run_until_complete(event.get_vehicle())

    assert event._get.called
    assert len(event._get.mock_calls) == 1
    assert event._get.mock_calls[0][1][0] == \
        'https://api.automatic.com/vehicle/mock_vehicle_id'
    assert vehicle.id == 'mock_vehicle_id'
    assert vehicle.url == 'mock_vehicle_url'
    assert vehicle.display_name == 'mock_display_name'


def test_realtime_get_device(client):
    """Test getting device information."""
    event = data.BaseRealtimeEvent(client, {
        'id': 'mock_id',
        'user': {
            'id': 'mock_user_id',
            'url': 'mock_user_url',
            },
        'type': 'location:updated',
        'vehicle': {
            'id': 'mock_vehicle_id',
            'url': 'mock_vehicle_url',
            },
        'device': {
            'id': 'mock_device_id',
            },
    })
    event._get = AsyncMock()
    resp = {
        'id': 'mock_device_id',
        'url': 'mock_device_url',
        'version': 2,
    }
    event._get.return_value = resp

    device = client.loop.run_until_complete(event.get_device())

    assert event._get.called
    assert len(event._get.mock_calls) == 1
    assert event._get.mock_calls[0][1][0] == \
        'https://api.automatic.com/device/mock_device_id'
    assert device.id == 'mock_device_id'
    assert device.url == 'mock_device_url'
    assert device.version == 2
