# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
from django.conf.urls import url
from django.core.handlers.base import BaseHandler
from django.http import HttpResponse
from django.http.response import Http404
from django.test.utils import override_settings
from django.utils.encoding import force_text

from shuup.admin.error_handlers import AdminPageErrorHandler
from shuup.admin.views.dashboard import DashboardView
from shuup.core.error_handling import install_error_handlers
from shuup.front.error_handlers import FrontPageErrorHandler
from shuup.front.views.index import IndexView
from shuup.utils.django_compat import get_resolver
from shuup_tests.utils import replace_urls


def setup_function(fn):
    # clear the cache for error handlers
    import shuup.core.error_handling as error_handling

    error_handling._URLCONF_ERROR_HANDLERS.clear()


def errorful_view(request, *args, **kwargs):
    raise Exception("Error! Aaargh.")  # The Castle of.


def notfound_view(request, *args, **kwargs):
    raise Http404("Error! Ops!")


def handler500(request, *args, **kwargs):
    return HttpResponse("Error! The best error.", status=500)


def four_oh_four(request, *args, **kwargs):
    return HttpResponse("Error! Just a flesh wound.", status=404)


def test_front_error_handlers(rf):
    """
    Test that `SHUUP_ERROR_PAGE_HANDLERS_SPEC` installs error handlers that are overwriting custom ones.
    """
    with override_settings(
        DEBUG=False,
        SHUUP_ERROR_PAGE_HANDLERS_SPEC=["shuup.front.error_handlers.FrontPageErrorHandler"],
        MIDDLEWARE_CLASSES=[],  # For Django < 2
        MIDDLEWARE=[],
        TEMPLATES=[  # Overriden to be sure about the contents of our 500.jinja
            {
                "BACKEND": "django_jinja.backend.Jinja2",
                "DIRS": [os.path.realpath(os.path.join(os.path.dirname(__file__), "templates"))],
                "OPTIONS": {
                    "match_extension": ".jinja",
                    "newstyle_gettext": True,
                },
                "NAME": "jinja2",
            }
        ],
    ):
        with replace_urls(
            [
                url("^aaargh/", errorful_view),
                url("^notfound/", notfound_view),
                url("^dash/", DashboardView.as_view()),
                url("^index/", IndexView.as_view()),
            ],
            {"handler404": four_oh_four, "handler500": handler500},
        ):
            resolver = get_resolver(None)
            urlconf = resolver.urlconf_module
            handler = BaseHandler()
            handler.load_middleware()

            # test without installing the handler
            assert urlconf.handler404 == four_oh_four
            assert urlconf.handler500 == handler500

            # Test 500
            response = handler.get_response(rf.get("/aaargh/"))
            assert response.status_code == 500
            assert b"The best error" in response.content
            # Test 404
            response = handler.get_response(rf.get("/another_castle/"))
            assert response.status_code == 404
            assert b"flesh wound" in response.content

            # inject our custom error handlers
            install_error_handlers()
            assert urlconf.handler404 != four_oh_four
            assert urlconf.handler500 != handler500
            assert "miss something? 404" in force_text(urlconf.handler404(rf.get("/notfound/")).content)
            assert "intergalactic testing 500" in force_text(urlconf.handler500(rf.get("/aaargh/")).content)

            # Front must handle all possible apps
            error_handler = FrontPageErrorHandler()

            response = handler.get_response(rf.get("/aaargh/"))
            assert "intergalactic testing 500" in force_text(response.content)

            # simulate a view to check whether the handler can handle an
            # error of a non-front view, a front view and a admin view
            for path in ("/aaargh/", "/index/", "/dash/"):
                request = rf.get(path)
                assert error_handler.can_handle_error(request, 500)
                assert error_handler.can_handle_error(request, 400)
                assert error_handler.can_handle_error(request, 403)
                assert error_handler.can_handle_error(request, 404)

                # check the error handlers return the correct status and text
                for status, content in [
                    (500, "intergalactic testing 500"),
                    (400, "about 400"),
                    (403, "get out 403"),
                    (404, "miss something? 404"),
                ]:
                    response = error_handler.handle_error(request, status)
                    assert response.status_code == status
                    assert content in force_text(response.content)

            from django.conf import settings

            # front can't handle static and media paths
            for path in (settings.STATIC_URL + "mystaticfile", settings.MEDIA_URL + "mymediafile"):
                request = rf.get(path)
                assert error_handler.can_handle_error(request, 500) is False
                assert error_handler.can_handle_error(request, 400) is False
                assert error_handler.can_handle_error(request, 403) is False
                assert error_handler.can_handle_error(request, 404) is False


def test_admin_error_handlers(rf):
    """
    Test that SHUUP_ERROR_PAGE_HANDLERS_SPEC installs error handlers that are overwriting custom ones.
    """
    with override_settings(
        DEBUG=False,
        SHUUP_ERROR_PAGE_HANDLERS_SPEC=["shuup.admin.error_handlers.AdminPageErrorHandler"],
        MIDDLEWARE_CLASSES=[],  # For Django 2
        MIDDLEWARE=[],
        TEMPLATES=[  # Overriden to be sure about the contents of our 500.jinja
            {
                "BACKEND": "django_jinja.backend.Jinja2",
                "DIRS": [os.path.realpath(os.path.join(os.path.dirname(__file__), "templates"))],
                "OPTIONS": {
                    "match_extension": ".jinja",
                    "newstyle_gettext": True,
                },
                "NAME": "jinja2",
            }
        ],
    ):
        with replace_urls(
            [
                url("^aaargh/", errorful_view),
                url("^index/", IndexView.as_view()),
                url("^dash/", DashboardView.as_view()),
            ],
            {"handler404": four_oh_four, "handler500": handler500},
        ):
            resolver = get_resolver(None)
            urlconf = resolver.urlconf_module
            handler = BaseHandler()
            handler.load_middleware()

            # test without installing the handler
            assert urlconf.handler404 == four_oh_four
            assert urlconf.handler500 == handler500

            # Test 500
            response = handler.get_response(rf.get("/aaargh/"))
            assert response.status_code == 500
            assert b"The best error" in response.content
            # Test 404
            response = handler.get_response(rf.get("/another_castle/"))
            assert response.status_code == 404
            assert b"flesh wound" in response.content

            # inject our custom error handlers
            install_error_handlers()

            # here the urlconfs will be the default handlers
            # because admin can't handle such requests
            # but the functions of the handlers are pointing to our factory view
            assert urlconf.handler404 != four_oh_four
            assert urlconf.handler500 != handler500
            assert "flesh wound" in force_text(urlconf.handler404(rf.get("/notfound/")).content)
            assert "The best error" in force_text(urlconf.handler500(rf.get("/aaargh/")).content)

            # Admin must handle only admin app errors
            error_handler = AdminPageErrorHandler()

            # simulate a view to check whether the handler can handle an error of a non-front view
            # Admin handler will check for the resolver_match and admin app only
            response = handler.get_response(rf.get("/aaargh/"))
            assert b"The best error" in response.content

            # can't handle non admin views neither media or static files
            from django.conf import settings

            for path in (
                "/aaargh/",
                "/index/",
                settings.STATIC_URL + "mystaticfile",
                settings.MEDIA_URL + "mymediafile",
            ):
                request = rf.get(path)
                assert error_handler.can_handle_error(request, 500) is False
                assert error_handler.can_handle_error(request, 400) is False
                assert error_handler.can_handle_error(request, 403) is False
                assert error_handler.can_handle_error(request, 404) is False

            # simulate a view to check whether the handler can handle an error of an admin view
            request = rf.get("/dash/")
            assert error_handler.can_handle_error(request, 500) is False
            assert error_handler.can_handle_error(request, 400) is False
            assert error_handler.can_handle_error(request, 403) is False
            assert error_handler.can_handle_error(request, 404) is False

            # check the error handlers return the correct status and text
            for status, content in [
                (500, "admin 500"),
                (400, "admin 400"),
                (403, "admin 403"),
                (404, "admin 404"),
            ]:
                response = error_handler.handle_error(request, status)
                assert response.status_code == status
                assert content in force_text(response.content)


def test_install_error_handlers(rf):
    # no error handler set
    with override_settings(DEBUG=False, SHUUP_ERROR_PAGE_HANDLERS_SPEC=[], MIDDLEWARE_CLASSES=[], MIDDLEWARE=[]):

        def intact_view(request, *args, **kwargs):
            return HttpResponse("OK")

        # set handlers in root urlconf
        with replace_urls(
            [
                url("^/", intact_view),
            ],
            {
                "handler400": intact_view,
                "handler403": intact_view,
                "handler404": intact_view,
                "handler500": intact_view,
            },
        ):
            # install error handlers - as soon as no spec was set,
            # the handlers must return the same as the default handlers
            install_error_handlers()

            resolver = get_resolver(None)
            urlconf = resolver.urlconf_module

            assert urlconf.handler500 != intact_view
            assert urlconf.handler400 != intact_view
            assert urlconf.handler403 != intact_view
            assert urlconf.handler404 != intact_view

            request = rf.get("/")
            assert urlconf.handler400(request).content == intact_view(request).content
            assert urlconf.handler403(request).content == intact_view(request).content
            assert urlconf.handler404(request).content == intact_view(request).content
            assert urlconf.handler500(request).content == intact_view(request).content

        # force clear again
        import shuup.core.error_handling as error_handling

        error_handling._URLCONF_ERROR_HANDLERS.clear()

        # NO handler set in root urlconf
        with replace_urls(
            [
                url("^aaargh/", errorful_view),
                url("^notfound/", notfound_view),
            ],
            {},
        ):
            # install error handlers - as soon as no spec was set,
            # neither handlers set in urlconf, must return blank http responses with errors
            install_error_handlers()

            resolver = get_resolver(None)
            urlconf = resolver.urlconf_module

            request = rf.get("/")
            assert urlconf.handler400(request).status_code == 400
            assert urlconf.handler403(request).status_code == 403
            assert urlconf.handler404(request).status_code == 404
            assert urlconf.handler500(request).status_code == 500

            handler = BaseHandler()
            handler.load_middleware()

            response = handler.get_response(rf.get("/aaargh/"))
            assert response.status_code == 500

            response = handler.get_response(rf.get("/notfound/"))
            assert response.status_code == 404
