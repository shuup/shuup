# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from django.utils.encoding import force_text
import pytest
from shoop.xtheme.theme import override_current_theme_class
from shoop.xtheme.views.extra import extra_view_dispatch
from shoop_tests.xtheme.utils import H2G2Theme


def test_xtheme_extra_views(rf):
    with override_current_theme_class(H2G2Theme):
        request = rf.get("/", {"name": "Arthur Dent"})
        # Simulate /xtheme/greeting
        response = extra_view_dispatch(request, "greeting")
        assert force_text(response.content) == "So long, and thanks for all the fish, Arthur Dent"
        # Try that again (to exercise the _VIEW_CACHE code path):
        response = extra_view_dispatch(request, "greeting")
        assert force_text(response.content) == "So long, and thanks for all the fish, Arthur Dent"
        # Now test that CBVs work
        assert not extra_view_dispatch(request, "faux").content


def test_xtheme_extra_view_exceptions(rf):
    with override_current_theme_class(H2G2Theme):
        request = rf.get("/")
        assert extra_view_dispatch(request, "vogons").status_code == 404
        with pytest.raises(ImproperlyConfigured):
            assert extra_view_dispatch(request, "true")
