import os

from django.conf.urls import url
from django.core.handlers.base import BaseHandler
from django.core.urlresolvers import get_resolver
from django.http import HttpResponse
from django.test.utils import override_settings
from django.utils.encoding import force_text

from shuup.front.error_handling import install_error_handlers
from shuup_tests.utils import replace_urls


def errorful_view(request, *args, **kwargs):
    raise Exception("Aaargh")  # The Castle of.


def four_oh_four(request, *args, **kwargs):
    return HttpResponse("Just a flesh wound")


def test_error_handlers(rf):
    """
    Test that SHUUP_FRONT_INSTALL_ERROR_HANDLERS installs error handlers
    without overwriting possible custom ones.
    """
    with override_settings(
        DEBUG=False,
        SHUUP_FRONT_INSTALL_ERROR_HANDLERS=True,
        MIDDLEWARE_CLASSES=[],
        TEMPLATES=[  # Overriden to be sure about the contents of our 500.jinja
            {
                "BACKEND": "django_jinja.backend.Jinja2",
                "DIRS": [
                    os.path.realpath(os.path.join(os.path.dirname(__file__), "templates"))
                ],
                "OPTIONS": {
                    "match_extension": ".jinja",
                    "newstyle_gettext": True,
                },
                "NAME": "jinja2",
            }
        ]
    ):
        with replace_urls([
            url("^aaargh/", errorful_view)
        ], {"handler404": four_oh_four}):
            resolver = get_resolver(None)
            urlconf = resolver.urlconf_module
            install_error_handlers()
            assert callable(urlconf.handler500)  # We get a new 500 handler
            assert urlconf.handler404 == four_oh_four  # Our custom 404 handler didn't get overwritten
            handler = BaseHandler()
            handler.load_middleware()
            # Test 500
            response = handler.get_response(rf.get("/aaargh/"))
            assert response.status_code == 500  # Uh oh!
            assert "intergalactic testing 500" in force_text(response.content)
            # Test 404
            response = handler.get_response(rf.get("/another_castle/"))
            assert response.status_code == 200  # Our custom 404 handler made it a 200!
            assert b"flesh wound" in response.content
