===============================
aioautomatic
===============================


.. image:: https://img.shields.io/pypi/v/aioautomatic.svg
        :target: https://pypi.python.org/pypi/aioautomatic

.. image:: https://img.shields.io/travis/armills/aioautomatic.svg
        :target: https://travis-ci.org/armills/aioautomatic

.. image:: https://img.shields.io/coveralls/armills/aioautomatic.svg
        :target: https://coveralls.io/r/armills/aioautomatic?branch=master

Asyncio library for the Automatic API


* Free software: Apache Software License 2.0

All methods are python wrappers of the API definitions defined by `Automatic <https://developer.automatic.com/api-reference/>`_.


Usage
-----

It is recommended to manage the aiohttp ClientSession object externally and pass it to the Client constructor. `(See the aiohttp documentation.) <https://aiohttp.readthedocs.io/en/stable/client_reference.html#aiohttp.ClientSession>`_ If not passed to Server, a ClientSession object will be created automatically.

Query for information from the users account.

.. code-block:: python

    import asyncio
    import aioautomatic
    import aiohttp
    from datetime import datetime
    from datetime import timedelta

    SCOPE = ['location', 'vehicle:profile', 'user:profile', 'trip']


    @asyncio.coroutine
    def loop():
        aiohttp_session = aiohttp.ClientSession()
        try:
            client = aioautomatic.Client(
                '<client_id>',
                '<secret>',
                aiohttp_session)
            session = yield from client.create_session_from_password(
                    SCOPE, '<user_email>', '<user_password>')

            # Fetch information about the authorized user
            user = yield from session.get_user()
            user_profile = yield from user.get_profile()
            user_metadata = yield from user.get_metadata()
            print("***USER***")
            print(user)
            print(user.email)
            print(user.first_name)
            print(user.last_name)
            print(user_profile.date_joined)
            print(user_metadata.firmware_version)
            print(user_metadata.device_type)
            print(user_metadata.phone_platform)

            # Fetch all devices associated with the user account
            devices = yield from session.get_devices()
            print("***DEVICES***")
            print(devices)

            # Fetch a list of vehicles associated with the user account
            vehicles = yield from session.get_vehicles()
            print("***VEHICLES***")
            print(vehicles)
            print(vehicles[0].make)
            print(vehicles[0].model)
            print(vehicles[0].fuel_level_percent)

            # Fetch a list of all trips in the last 10 days
            min_end_time = datetime.utcnow() - timedelta(days=10)
            trips = yield from session.get_trips(ended_at__gte=min_end_time, limit=10)
            print("***TRIPS***")
            print(trips)
            print(trips[0].start_location.lat)
            print(trips[0].start_location.lon)
            print(trips[0].start_address.name)
            print(trips[0].distance_m)
            print(trips[0].duration_s)

            # If more than 10 trips exist, get the next page of results
            if trips.next is not None:
                trips = yield from trips.get_next()
                print(trips)

        finally:
            yield from aiohttp_session.close()

    asyncio.get_event_loop().run_until_complete(loop())

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

