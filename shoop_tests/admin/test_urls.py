# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from collections import Counter

import pytest
from django.core.exceptions import ImproperlyConfigured

from shoop.admin.utils.urls import admin_url, get_model_url, NoModelUrl
from shoop.core.models import Product
from shoop_tests.admin.utils import admin_only_urls


def test_model_url():
    with admin_only_urls():
        with pytest.raises(NoModelUrl):
            get_model_url(Counter)  # That's silly!
        p = Product()
        p.pk = 3
        assert get_model_url(p)


def test_invalid_admin_url():
    with pytest.raises(ImproperlyConfigured):
        admin_url("", "")


def test_admin_url_prefix():
    assert admin_url("", "foo", prefix="bar")._callback_str == "bar.foo"
