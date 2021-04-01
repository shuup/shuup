# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup
from django.utils.encoding import force_text

from shuup.admin.modules.shops.views.edit import ShopEditView
from shuup.apps.provides import override_provides
from shuup.testing.factories import create_random_person, get_default_shop
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_shop_edit_has_custom_toolbar_button(rf, admin_user):
    shop = get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = ShopEditView.as_view()
    response = view_func(request, pk=shop.pk)
    content = force_text(response.render().content)
    assert "#mocktoolbarbuttonforshop" in content, "custom toolbar button not found on edit page"
