# -*- coding: utf-8 -*-
from django_jinja.builtins import DEFAULT_EXTENSIONS

import os
import re

import six
from django.contrib.auth.models import AnonymousUser
from django.test.client import RequestFactory
from django.views.generic import View
from django_jinja.backend import Jinja2

from shoop.apps.provides import override_provides
from shoop.xtheme.editing import is_edit_mode, set_edit_mode
from shoop.xtheme.view_config import Layout
from shoop.xtheme import parsing
from shoop_tests.utils import printable_gibberish
from shoop_tests.utils.faux_users import SuperUser

CLOSE_ENOUGH_FIX_RE = re.compile("[\s]+")
TEST_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def get_jinja2_engine():
    extensions = list(DEFAULT_EXTENSIONS) + list(parsing.EXTENSIONS)
    return Jinja2({
        "DIRS": [TEST_TEMPLATE_DIR],
        "APP_DIRS": False,
        "OPTIONS": {
            "match_extension": ".jinja",
            "context_processors": (),
            "environment": "shoop.xtheme.engine.XthemeEnvironment",
            "extensions": extensions
        },
        "NAME": "jinja2",
    })


def close_enough(sa, sb):
    """
    Compare two strings and return true if they're the same notwithstanding any whitespace or case.
    """
    sa = CLOSE_ENOUGH_FIX_RE.sub("", six.text_type(sa)).lower()
    sb = CLOSE_ENOUGH_FIX_RE.sub("", six.text_type(sb)).lower()
    return (sa == sb)


class FauxView(View):
    pass


def get_test_template_bits(request, pass_view=True, **extra_ctx):
    layout = Layout("test")
    gibberish = printable_gibberish()
    layout.begin_column({"md": 12, "xs": 0})
    layout.add_plugin("text", {"text": gibberish})
    jeng = get_jinja2_engine()
    template = jeng.from_string("")
    template.template.name = "test"
    vars = {
        "view": pass_view and FauxView(),
        "request": request
    }
    vars.update(extra_ctx)
    ctx = template.template.new_context(vars)
    return (template, layout, gibberish, ctx)




def get_request(edit=False):
    request = RequestFactory().get("/")
    request.session = {}
    if edit:
        request.user = SuperUser()
        set_edit_mode(request, True)
        assert is_edit_mode(request)
    else:
        request.user = AnonymousUser()
    return request


def plugin_override():
    return override_provides("xtheme_plugin", [
        "shoop.xtheme.plugins.text:TextPlugin",
    ])
