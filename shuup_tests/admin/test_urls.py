# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from collections import Counter
from django.core.exceptions import ImproperlyConfigured
from mock import patch

from shuup.admin.utils.permissions import set_permissions_for_group
from shuup.admin.utils.urls import NoModelUrl, admin_url, get_model_url
from shuup.testing.factories import get_default_product, get_default_shop, get_default_staff_user
from shuup_tests.admin.utils import admin_only_urls


@pytest.mark.django_db
def test_model_url():
    with admin_only_urls():
        with pytest.raises(NoModelUrl):
            get_model_url(Counter)  # That's silly!
        p = get_default_product()

        assert get_model_url(p, shop=get_default_shop())


@pytest.mark.django_db
def test_model_url_with_permissions():
    permissions = set(["shop_product.new", "shop_product.delete", "shop_product.edit"])
    shop = get_default_shop()
    p = get_default_product()

    # If no user is given, don't check for permissions
    assert get_model_url(p, shop=shop)

    # If a user is given and no permissions are provided, check for default model permissions
    user = get_default_staff_user()
    with pytest.raises(NoModelUrl):
        assert get_model_url(p, user=user, shop=shop)

    # If a user is given and permissions are provided, check for those permissions
    assert get_model_url(p, user=user, required_permissions=(), shop=shop)
    with pytest.raises(NoModelUrl):
        assert get_model_url(p, user=user, required_permissions=["shop_product.new"], shop=shop)

    # Confirm that url is returned with correct permissions
    set_permissions_for_group(user.groups.first(), permissions)
    assert get_model_url(p, user=user, shop=shop)
    assert get_model_url(p, user=user, required_permissions=permissions, shop=shop)


def test_invalid_admin_url():
    with pytest.raises(ImproperlyConfigured):
        admin_url("", "")


class TestMagic(object):
    def __call__(self):
        return


@patch("shuup.utils.importing.load", autospec=TestMagic)
def test_admin_url_prefix(conf_get_mock):
    admin_url("", "foo", prefix="bar")
    conf_get_mock.assert_called_once_with("bar.foo")
