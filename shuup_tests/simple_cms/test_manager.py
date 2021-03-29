# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from shuup.simple_cms.models import Page
from shuup.testing.factories import get_default_shop
from shuup_tests.simple_cms.utils import create_page


@pytest.mark.django_db
def test_suppliers_manager(admin_user):
    shop = get_default_shop()
    page = create_page(url="bacon", shop=get_default_shop())

    assert Page.objects.visible(shop).count() == 1
    assert Page.objects.visible(shop, user=admin_user).count() == 1
    page.soft_delete(admin_user)
    assert Page.objects.visible(shop).count() == 0


@pytest.mark.django_db
def test_suppliers_deleted(admin_user):
    page = create_page(url="bacon", shop=get_default_shop())

    with pytest.raises(NotImplementedError):
        page.delete()

    page.soft_delete(admin_user)
    assert page.deleted is True
