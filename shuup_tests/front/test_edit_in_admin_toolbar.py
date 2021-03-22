# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup

from shuup.admin.utils.urls import get_model_url
from shuup.front.views.category import CategoryView
from shuup.front.views.product import ProductDetailView
from shuup.simple_cms.views import PageView
from shuup.testing.factories import get_default_category, get_default_product, get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup_tests.simple_cms.utils import create_page


@pytest.mark.parametrize(
    "view, function", [(ProductDetailView, get_default_product), (CategoryView, get_default_category)]
)
@pytest.mark.django_db
def test_edit_in_admin_url(rf, view, function, admin_user):
    shop = get_default_shop()  # obvious prerequisite
    shop.staff_members.add(admin_user)
    model = function()  # call the function get_default_model
    view_func = view.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view_func(request, pk=model.pk)
    response.render()
    content = response.content
    soup = BeautifulSoup(content)
    check_url(soup, model)


@pytest.mark.django_db
def test_edit_page_in_admin_toolbar(rf, admin_user):
    shop = get_default_shop()  # test
    shop.staff_members.add(admin_user)
    model = create_page(shop=shop)
    view = PageView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request, url=model.url)
    response.render()
    content = response.content
    soup = BeautifulSoup(content)
    check_url(soup, model)


def check_url(soup, model):
    ul = soup.find("ul", class_="nav navbar-nav navbar-right")
    a = ul.find_all("li")[0].find("a")
    assert a.get("href") == get_model_url(model)
