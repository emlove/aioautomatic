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


class Vehicle(base.BaseDataObject):
    """Vehicle object to manage access to a vehicle information."""
    validator = validation.VEHICLE


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


class Device(base.BaseDataObject):
    """Device object to manage access to a device information."""
    validator = validation.DEVICE


class User(base.BaseApiObject, base.BaseDataObject):
    """User object to manage access to user information."""
    validator = validation.USER

    def __init__(self, session, data):
        """Create the data object."""
        base.BaseApiObject.__init__(self, session)
        base.BaseDataObject.__init__(self, data)

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
