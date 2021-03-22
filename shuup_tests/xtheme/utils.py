# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import re
import six
from django.contrib.auth.models import AnonymousUser
from django.http.response import HttpResponse
from django.test.client import RequestFactory
from django.views.generic import View
from django_jinja.backend import Jinja2
from django_jinja.builtins import DEFAULT_EXTENSIONS

from shuup.apps.provides import override_provides
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup.xtheme import Theme, parsing
from shuup.xtheme.editing import is_edit_mode, set_edit_mode
from shuup.xtheme.view_config import Layout
from shuup_tests.utils import printable_gibberish
from shuup_tests.utils.faux_users import SuperUser

CLOSE_ENOUGH_FIX_RE = re.compile("[\s]+")
TEST_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def get_jinja2_engine():
    extensions = list(DEFAULT_EXTENSIONS) + list(parsing.EXTENSIONS)
    return Jinja2(
        {
            "DIRS": [TEST_TEMPLATE_DIR],
            "APP_DIRS": False,
            "OPTIONS": {
                "match_extension": ".jinja",
                "context_processors": (),
                "environment": "shuup.xtheme.engine.XthemeEnvironment",
                "extensions": extensions,
            },
            "NAME": "jinja2",
        }
    )


def close_enough(sa, sb):
    """
    Compare two strings and return true if they're the same notwithstanding any whitespace or case.
    """
    sa = CLOSE_ENOUGH_FIX_RE.sub("", six.text_type(sa)).lower()
    sb = CLOSE_ENOUGH_FIX_RE.sub("", six.text_type(sb)).lower()
    return sa == sb


class FauxView(View):
    pass


class FauxTheme(Theme):
    identifier = "testing_faux_theme"


class FauxTheme2(Theme):
    identifier = "testing_faux_theme_too"


def greeting_view(request):
    return HttpResponse("So long, and thanks for all the fish, %s" % request.GET.get("name", "Humanity"))


class H2G2Theme(Theme):
    template_dir = "h2g2"
    identifier = "h2g2"

    def get_view(self, view_name):
        return {"greeting": greeting_view, "faux": FauxView, "true": True}.get(view_name)


def get_test_template_bits(request, pass_view=True, **extra_ctx):
    layout = Layout(FauxTheme, "test")
    gibberish = printable_gibberish()
    layout.begin_column({"md": 12, "xs": -1})
    layout.add_plugin("text", {"text": "<p>%s</p>" % gibberish})
    jeng = get_jinja2_engine()
    template = jeng.from_string("")
    template.template.name = "test"
    vars = {"view": pass_view and FauxView(), "request": request}
    vars.update(extra_ctx)
    ctx = template.template.new_context(vars)
    return (template, layout, gibberish, ctx)


def get_request(edit=False):
    get_default_shop()
    request = apply_request_middleware(RequestFactory().get("/"))
    request.session = {}
    if edit:
        request.user = SuperUser()
        set_edit_mode(request, True)
        assert is_edit_mode(request)
    else:
        request.user = AnonymousUser()
    return request


def plugin_override():
    return override_provides(
        "xtheme_plugin",
        ["shuup.xtheme.plugins.text:TextPlugin", "shuup_tests.xtheme.test_resources:ResourceInjectorPlugin"],
    )


def layout_override():
    return override_provides("xtheme_layout", [])
