# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django import forms
from django.test import override_settings

from shuup.core import cache, shop_provider
from shuup.core.models import Supplier
from shuup.front.forms.product_list_modifiers import CommaSeparatedListField
from shuup.front.forms.product_list_supplier_modifier import SupplierProductListFilter
from shuup.front.utils.sorts_and_filters import get_configuration, set_configuration
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_suppliers_filter_get_fields(rf):
    cache.clear()
    shop = factories.get_default_shop()

    request = apply_request_middleware(rf.get("/"))
    assert SupplierProductListFilter().get_fields(request, None) is None

    supplier = Supplier.objects.create(name="Favorite brands dot com")
    supplier.shops.add(shop)
    assert Supplier.objects.enabled().exists()
    assert SupplierProductListFilter().get_fields(request, None) is None

    category = factories.get_default_category()
    product = factories.create_product("sku", shop=shop)
    shop_product = product.get_shop_instance(shop=shop)
    shop_product.primary_category = category
    shop_product.save()

    assert SupplierProductListFilter().get_fields(request, category) is None

    # Now once we link supplier to product we should get
    # form field for manufacturer
    shop_product.suppliers.add(supplier)
    form_field = SupplierProductListFilter().get_fields(request, category)[0][1]
    assert form_field is not None
    assert form_field.label == "Suppliers"

    with override_settings(SHUUP_FRONT_OVERRIDE_SORTS_AND_FILTERS_LABELS_LOGIC={"supplier": "Filter by suppliers"}):
        form_field = SupplierProductListFilter().get_fields(request, category)[0][1]
        assert form_field is not None
        assert form_field.label == "Filter by suppliers"
        assert isinstance(form_field, forms.ModelChoiceField)

        configuration = get_configuration(shop, category)
        configuration.update({SupplierProductListFilter.enable_multiselect_key: True})

        set_configuration(shop, category, configuration)
        form_field = SupplierProductListFilter().get_fields(request, category)[0][1]
        assert form_field is not None
        assert form_field.label == "Filter by suppliers"
        assert isinstance(form_field, CommaSeparatedListField)

        cache.clear()
