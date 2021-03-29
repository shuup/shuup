# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test import override_settings

from shuup.core import cache
from shuup.core.models import Manufacturer
from shuup.front.forms.product_list_modifiers import ManufacturerProductListFilter
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_manufacturer_filter_get_fields(rf):
    cache.clear()

    shop = factories.get_default_shop()

    request = apply_request_middleware(rf.get("/"))
    assert ManufacturerProductListFilter().get_fields(request, None) is None

    manufacturer = Manufacturer.objects.create(name="Random Brand Inc")
    assert ManufacturerProductListFilter().get_fields(request, None) is None

    category = factories.get_default_category()
    product = factories.create_product("sku", shop=shop)
    shop_product = product.get_shop_instance(shop=shop)
    shop_product.primary_category = category
    shop_product.save()

    assert ManufacturerProductListFilter().get_fields(request, category) is None

    # Now once we link manufacturer to product we should get
    # form field for manufacturer
    product.manufacturer = manufacturer
    product.save()
    form_field = ManufacturerProductListFilter().get_fields(request, category)[0][1]
    assert form_field is not None
    assert form_field.label == "Manufacturers"

    with override_settings(SHUUP_FRONT_OVERRIDE_SORTS_AND_FILTERS_LABELS_LOGIC={"manufacturers": "Brands"}):
        form_field = ManufacturerProductListFilter().get_fields(request, category)[0][1]
        assert form_field is not None
        assert form_field.label == "Brands"
