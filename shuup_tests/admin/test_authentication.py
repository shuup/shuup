# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test import override_settings

from shuup.core.models import ShopStatus
from shuup.testing import factories
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
@override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True)
def test_staff_authentication():
    shop = factories.get_shop(True, "USD", enabled=True)
    staff_user = factories.create_random_user(is_staff=True)
    staff_user.set_password("randpw")
    staff_user.save()
    staff_user.groups.set([factories.get_default_permission_group()])
    shop.staff_members.add(staff_user)

    assert staff_user in [staff for staff in shop.staff_members.all()]
    assert shop.status == ShopStatus.ENABLED
    client = SmartClient()
    url = reverse("shuup_admin:dashboard")
    client.login(username=staff_user.username, password="randpw")
    response, soup = client.response_and_soup(url)
    assert response.status_code == 200

    shop.status = ShopStatus.DISABLED
    shop.save()

    response, soup = client.response_and_soup(url)
    assert response.status_code == 400
    assert "There is no active shop available" in soup.text
