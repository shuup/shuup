# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from django.utils.encoding import force_text

from shuup.xtheme.testing import override_current_theme_class
from shuup.xtheme.views.extra import extra_view_dispatch
from shuup_tests.xtheme.utils import H2G2Theme


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
