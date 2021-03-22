# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.apps.provides import override_provides
from shuup.core.models import get_person_contact
from shuup.front.basket import get_basket
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
def test_basket_line_descriptor(rf):
    shop = factories.get_default_shop()
    user = factories.create_random_user()
    supplier = factories.get_default_supplier()
    product = factories.create_product("product", shop, supplier, 10)

    client = SmartClient()
    response = client.post(
        path=reverse("shuup:basket"), data={"command": "add", "product_id": product.pk, "quantity": 1}
    )

    with override_provides(
        "front_line_properties_descriptor", ["shuup.testing.line_properties_descriptor.TestLinePropertiesDescriptor"]
    ):
        soup = client.soup(reverse("shuup:basket"))
        basket_line_property = soup.find("p", {"class": "basket-line-property"})
        assert basket_line_property.find("strong", {"class": "property-name"}).text.strip() == "Type:"
        assert basket_line_property.find("span", {"class": "property-value"}).text.strip() == "product"
