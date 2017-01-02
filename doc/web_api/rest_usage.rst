API Usage
=========

The API is JSON based, so you might expect the content type ``application/json`` from each response.

**Note**: *We really encourage you to only use the API through a secure connection (HTTPs) to avoid several cyber attacks.*

First of all, let's configure the Django Settings. This is our base settings snippet:

.. code-block:: python

    REST_FRAMEWORK = {
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.BasicAuthentication',
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        ),
        'DEFAULT_PERMISSION_CLASSES': (
            'shuup.api.permissions.ShuupAPIPermission',
        )
    }
    JWT_AUTH = {
        'JWT_ALLOW_REFRESH': True,
        'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=300)  # 5 minutes
    }


We use the `JSON Web Token`_ authentication method to avoid sending the username/e-mail and password on each request.

**Note**: *The following commands were generated using* `HTTPie`_, *an awesome command line HTTP client. We are cropping the JSON Token as our main purpose here is the usage itself.*

So, the first step is to authenticate and fetch a valid JSON Token to use on further requests:


.. code-block:: shell

    http POST http://localhost:8000/api/api-token-auth/ username=admin password=admin

    HTTP/1.0 200 OK
    Allow: POST, OPTIONS
    Content-Language: en
    Content-Type: application/json
    Vary: Accept, Accept-Language, Cookie
    X-Frame-Options: SAMEORIGIN

    {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }


Now we've got our token to use on further requests. Note that this token has a expiration time (by default it is 5 minutes).
This way, we should always refresh our token before it becomes invalid. To refresh our token, simply do:


.. code-block:: shell

    http POST http://localhost:8000/api/api-token-refresh/ token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

    HTTP/1.0 200 OK
    Allow: POST, OPTIONS
    Content-Language: en
    Content-Type: application/json
    Vary: Accept, Accept-Language, Cookie
    X-Frame-Options: SAMEORIGIN

    {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }


**Note**: *Remember to fresh the token before each* ``JWT_EXPIRATION_DELTA`` *minutes.*

Now it is time to use our token to make useful things. Let's fetch Product Types:

.. code-block:: shell

    http GET http://localhost:8000/api/shuup/product_type/ Authorization:"JWT YOUR_TOKEN_HERE"

    HTTP/1.0 200 OK
    Allow: GET, POST, OPTIONS
    Content-Language: en
    Content-Type: application/json
    Vary: Accept, Accept-Language, Cookie
    X-Frame-Options: SAMEORIGIN

    [
        {
            "attributes": [],
            "id": 1,
            "identifier": "default",
            "translations": {
                "en": {
                    "name": "Standard Product"
                }
            }
        }
    ]


And now we need a new Manufacturer:


.. code-block:: shell

    http POST http://localhost:8000/api/shuup/manufacturer/ Authorization:"JWT YOUR_TOKEN_HERE" name="New Manufacturer" url=http://new-manuf.com

    HTTP/1.0 201 Created
    Allow: GET, POST, OPTIONS
    Content-Language: en
    Content-Type: application/json
    Vary: Accept, Accept-Language, Cookie
    X-Frame-Options: SAMEORIGIN

    {
        "created_on": "2017-01-02T18:30:30.549831Z",
        "id": 1,
        "name": "New Manufacturer",
        "url": "http://new-manuf.com"
    }


**Note**: *Remember to use the* ``application/json`` *content type on your requests when using the API within your code.*


.. _JSON Web Token: https://github.com/GetBlimp/django-rest-framework-jwt
.. _HTTPie: https://httpie.org/
