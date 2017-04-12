===============================
aioautomatic
===============================


.. image:: https://img.shields.io/pypi/v/aioautomatic.svg
        :target: https://pypi.python.org/pypi/aioautomatic

.. image:: https://img.shields.io/travis/armills/aioautomatic.svg
        :target: https://travis-ci.org/armills/aioautomatic

.. image:: https://pyup.io/repos/github/armills/aioautomatic/shield.svg
     :target: https://pyup.io/repos/github/armills/aioautomatic/
     :alt: Updates


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

    @asyncio.coroutine
    def loop():
        aiohttp_session = aiohttp.ClientSession()
        try:
            client = aioautomatic.Client(
                '<client_id>',
                '<secret>',
                aiohttp_session)
            session = yield from client.create_session_from_password(
                    '<user_email>', '<user_password>')
            vehicles = yield from session.get_vehicles()
            print(vehicles)
            min_end_time = datetime.utcnow() - timedelta(days=1)
            trips = yield from session.get_trips(ended_at__gte=min_end_time, limit=10)
            print(trips)
        finally:
            yield from aiohttp_session.close()

    asyncio.get_event_loop().run_until_complete(loop())

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

