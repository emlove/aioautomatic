"""Data interface classes for aioautomatic."""
import asyncio
import logging

from aioautomatic import base
from aioautomatic import const
from aioautomatic import validation

_LOGGER = logging.getLogger(__name__)


class Address(base.BaseDataObject):
    """Address object representing a trip address."""
    validator = validation.ADDRESS


class Location(base.BaseDataObject):
    """Location object representing GPS coordinates."""
    validator = validation.LOCATION


class VehicleEvent(base.BaseDataObject):
    """Object representing a vehicle event."""
    validator = validation.VEHICLE_EVENT


class VehicleDTCS(base.BaseDataObject):
    """Object representing a vehicle DTCS code."""
    validator = validation.VEHICLE_DTCS


class Vehicle(base.BaseDataObject):
    """Vehicle object to manage access to a vehicle information."""
    validator = validation.VEHICLE

    def __init__(self, data):
        """Create the data object."""
        super().__init__(data)
        self.active_dtcs = [
            VehicleDTCS(v) for v in self._data.get('active_dtcs') or []]


class Trip(base.BaseDataObject):
    """Trip object to manage access to a trip information."""

    validator = validation.TRIP

    def __init__(self, data):
        """Create the data object."""
        super().__init__(data)
        self.start_location = Location(self._data.get('start_location'))
        self.start_address = Address(self._data.get('start_address'))
        self.end_location = Location(self._data.get('end_location'))
        self.end_address = Address(self._data.get('end_address'))
        self.vehicle_events = [
            VehicleEvent(ev) for ev in self._data.get('vehicle_events')]
        self.tags = self._data.get('tags') or []


class Device(base.BaseDataObject):
    """Device object to manage access to a device information."""
    validator = validation.DEVICE


class User(base.BaseApiDataObject):
    """User object to manage access to user information."""
    validator = validation.USER

    @asyncio.coroutine
    def get_profile(self):
        """Fetch profile information for this user."""
        _LOGGER.info("Fetching user profile.")
        resp = yield from self._get(const.USER_PROFILE_URL.format(self.id))
        return UserProfile(resp)

    @asyncio.coroutine
    def get_metadata(self):
        """Fetch metadata information for this user."""
        _LOGGER.info("Fetching user metadata.")
        resp = yield from self._get(const.USER_METADATA_URL.format(self.id))
        return UserMetadata(resp)


class UserProfile(base.BaseDataObject):
    """User profile object to manage access to user information."""
    validator = validation.USER_PROFILE


class UserMetadata(base.BaseDataObject):
    """User metadata object to manage access to user information."""
    validator = validation.USER_METADATA


class RealtimeDevice(base.BaseDataObject):
    """Object to save the device id."""
    validator = validation.REALTIME_DEVICE


class RealtimeLocation(base.BaseDataObject):
    """Location object representing GPS coordinates."""
    validator = validation.REALTIME_LOCATION


class BaseRealtimeEvent(base.BaseApiDataObject):
    """Realtime event object"""
    validator = validation.REALTIME_BASE

    def __init__(self, client, data):
        """Create the data object."""
        super().__init__(client, data)
        self.user = User(client, self._data.get('user'))
        self.vehicle = Vehicle(self._data.get('vehicle'))
        self.device = RealtimeDevice(self._data.get('device'))
        if self._data.get('location') is not None:
            self.location = RealtimeLocation(self._data.get('location'))

    @asyncio.coroutine
    def get_user(self):
        """Fetch user object for this trip."""
        _LOGGER.info("Fetching user.")
        resp = yield from self._get(const.USER_URL.format(self.user.id))
        return User(self._parent, resp)

    @asyncio.coroutine
    def get_vehicle(self):
        """Fetch vehicle object for this trip."""
        _LOGGER.info("Fetching vehicle.")
        resp = yield from self._get(const.VEHICLE_URL.format(self.vehicle.id))
        return Vehicle(resp)

    @asyncio.coroutine
    def get_device(self):
        """Fetch device object for this trip."""
        _LOGGER.info("Fetching device.")
        resp = yield from self._get(const.DEVICE_URL.format(self.device.id))
        return Device(resp)


class RealtimeTripFinished(BaseRealtimeEvent):
    """Realtime trip finished event object"""
    validator = validation.REALTIME_TRIP_FINISHED


class RealtimeIgnitionOn(BaseRealtimeEvent):
    """Realtime ignition on event object"""


class RealtimeIgnitionOff(BaseRealtimeEvent):
    """Realtime ignition off event object"""


class RealtimeSpeeding(BaseRealtimeEvent):
    """Realtime speeding event object"""
    validator = validation.REALTIME_SPEEDING


class RealtimeHardBrake(BaseRealtimeEvent):
    """Realtime hard brake event object"""
    validator = validation.REALTIME_HARD_BRAKE


class RealtimeMILOn(BaseRealtimeEvent):
    """Realtime MIL on event object"""
    validator = validation.REALTIME_MIL_ON

    def __init__(self, client, data):
        """Create the data object."""
        super().__init__(client, data)
        self.dtcs = [
            VehicleDTCS(v) for v in self._data.get('dtcs') or []]


class RealtimeMILOff(BaseRealtimeEvent):
    """Realtime MIL off event object"""
    validator = validation.REALTIME_MIL_OFF


class RealtimeHardAccel(BaseRealtimeEvent):
    """Realtime hard acceleration event object"""
    validator = validation.REALTIME_HARD_ACCEL


class RealtimeLocationUpdated(BaseRealtimeEvent):
    """Realtime location updated event object"""


class RealtimeVehicleStatusReport(BaseRealtimeEvent):
    """Realtime vehicle status report event object"""


REALTIME_EVENT_CLASS = {
    'trip:finished': RealtimeTripFinished,
    'ignition:on': RealtimeIgnitionOn,
    'ignition:off': RealtimeIgnitionOff,
    'notification:speeding': RealtimeSpeeding,
    'notification:hard_brake': RealtimeHardBrake,
    'notification:hard_accel': RealtimeHardAccel,
    'mil:on': RealtimeMILOn,
    'mil:off': RealtimeMILOff,
    'location:updated': RealtimeLocationUpdated,
    'vehicle:status_report': RealtimeVehicleStatusReport,
}
