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

    CLIENT_ID = '<client_id>'
    SECRET_ID = '<secret>'
    SCOPE = ['current_location', 'location', 'vehicle:profile', 'user:profile', 'trip']


    @asyncio.coroutine
    def loop():
        aiohttp_session = aiohttp.ClientSession()
        try:
            client = aioautomatic.Client(
                CLIENT_ID,
                SECRET_ID,
                aiohttp_session)
            url = client.generate_oauth_url(SCOPE)

            # Redirect the user to this URL. After the user authorizes access
            # to their account, Automatic will redirect them to your
            # application's OAuth Redirect URL, configured in the Automatic
            # Developer Apps Manager. Capture the code and state returned
            # with that request.
            code = '<code>'
            state = '<state>'

            session = yield from client.create_session_from_oauth_code(
                code, state)

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

            # Save the refresh token from the session for use next time
            # a session needs to be created.
            refresh_token = session.refresh_token

            # Create a new session with the refresh token.
            session = yield from client.create_session_from_refresh_token(
                refresh_token)

        finally:
            yield from aiohttp_session.close()

    asyncio.get_event_loop().run_until_complete(loop())

Create a session using user credentials. (Not recommended)

.. code-block:: python

    import asyncio
    import aioautomatic
    import aiohttp

    SCOPE = ['location', 'vehicle:profile', 'user:profile', 'trip']

    CLIENT_ID = '<client_id>'
    SECRET_ID = '<secret>'
    USER_EMAIL = '<user_email>'
    USER_PASSWORD = '<user_password>'


    @asyncio.coroutine
    def loop():
        aiohttp_session = aiohttp.ClientSession()
        try:
            client = aioautomatic.Client(
                CLIENT_ID,
                SECRET_ID,
                aiohttp_session)
            session = yield from client.create_session_from_password(
                    SCOPE, USER_EMAIL, USER_PASSWORD)

            # Fetch information about the authorized user
            user = yield from session.get_user()
            user_profile = yield from user.get_profile()
            user_metadata = yield from user.get_metadata()
            print("***USER***")
            print(user)
            print(user.email)
            print(user.first_name)
            print(user.last_name)

        finally:
            yield from aiohttp_session.close()

    asyncio.get_event_loop().run_until_complete(loop())

Open a websocket connection for realtime updates

.. code-block:: python

    import asyncio
    import aioautomatic
    import aiohttp

    SCOPE = ['current_location', 'location', 'vehicle:profile', 'user:profile', 'trip']

    CLIENT_ID = '<client_id>'
    SECRET_ID = '<secret>'


    def error_callback(name, message):
        print(message)


    def event_callback(name, data):
        print(name)
        if data.location:
            print(data.location.lat)
            print(data.location.lon)


    def speeding_callback(name, data):
        print("Speeding! Velocity: {:1.2f} KPH".format(data.velocity_kph))


    @asyncio.coroutine
    def loop():
        aiohttp_session = aiohttp.ClientSession()
        try:
            client = aioautomatic.Client(
                CLIENT_ID,
                SECRET_ID,
                aiohttp_session)

            client.on('closed', closed_callback)
            client.on('notification:speeding', speeding_callback)
            client.on_app_event(callback)
            future = yield from client.ws_connect()

            # Run until websocket is closed
            yield from future

        finally:
            yield from aiohttp_session.close()

    asyncio.get_event_loop().run_until_complete(loop())

Changelog
---------
0.5.0 (Future)
~~~~~~~~~~~~~~
 - Added `Client.generate_oauth_url` to simplify implementation of OAuth2 authentication.
 - State is now required for `Client.create_session_from_oauth_code`.

Credits
---------

This package is built on aiohttp_, which provides the foundation for async HTTP and websocket calls.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _aiohttp: http://aiohttp.readthedocs.io/en/stable/
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

