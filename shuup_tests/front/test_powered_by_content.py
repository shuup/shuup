# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup
from django.test.utils import override_settings

from shuup.front.views.index import IndexView
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_edit_in_admin_url(rf):
    get_default_shop()
    soup = _get_front_soup(rf)
    _check_powered_by_href(soup, "https://shuup.com")
    with override_settings(SHUUP_FRONT_POWERED_BY_CONTENT='<p class="powered"><a href="123">456</a></p>'):
        soup = _get_front_soup(rf)
        _check_powered_by_href(soup, "123")

    with override_settings(SHUUP_FRONT_POWERED_BY_CONTENT=None):
        soup = _get_front_soup(rf)
        assert soup.find("p", {"class": "powered"}) is None


def _get_front_soup(rf):
    view_func = IndexView.as_view()
    request = apply_request_middleware(rf.get("/"))
    response = view_func(request)
    response.render()
    content = response.content
    return BeautifulSoup(content)


def _check_powered_by_href(soup, expected):
    assert soup.find("p", {"class": "powered"}).find("a")["href"] == expected
