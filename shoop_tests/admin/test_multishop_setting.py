# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.test import override_settings
import pytest

from shoop.admin.modules.shops.views.edit import ShopEditView
from shoop.testing.factories import get_default_shop
from shoop_tests.utils import apply_request_middleware
from shoop.utils.excs import Problem


@pytest.mark.django_db
def test_multishop_edit_view(rf, admin_user):
    get_default_shop()

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view = ShopEditView(request=request, kwargs={"pk": None}) 

    with override_settings(SHOOP_ENABLE_MULTIPLE_SHOPS=False):
        with pytest.raises(Problem):
            view.get_object()  # Now view object should throw Problem

    with override_settings(SHOOP_ENABLE_MULTIPLE_SHOPS=True):
        new_shop = view.get_object()
        assert new_shop.pk is None 
