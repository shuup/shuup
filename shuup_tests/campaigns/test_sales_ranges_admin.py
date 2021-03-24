# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from mock import patch

from shuup.admin.modules.contact_groups.views import ContactGroupEditView
from shuup.admin.modules.contact_groups.views.forms import ContactGroupBaseFormPart
from shuup.campaigns.models import ContactGroupSalesRange
from shuup.core.models import Shop, ShopStatus
from shuup.testing.factories import create_random_company, get_default_customer_group, get_default_shop, get_shop
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_form_part_for_new_group(rf, admin_user):
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    initialized_view = ContactGroupEditView(request=request, kwargs={"pk": None})
    initialized_view.object = initialized_view.get_object()  # Just for test
    form_def_values = initialized_view.get_form().form_defs.values()
    assert [form_def for form_def in form_def_values if form_def.name == "base"]
    # contact_group_sales_ranges should not be in form defs
    assert not [form_def for form_def in form_def_values if "contact_group_sales_ranges" in form_def.name]


@pytest.mark.django_db
def test_form_part_for_default_group(rf, admin_user):
    get_default_shop()
    company = create_random_company()
    group = company.get_default_group()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    initialized_view = ContactGroupEditView(request=request, kwargs={"pk": group.pk})
    initialized_view.object = initialized_view.get_object()  # Just for test
    form_def_values = initialized_view.get_form().form_defs.values()
    assert [form_def for form_def in form_def_values if form_def.name == "base"]
    # contact_group_sales_ranges should not be in form defs
    assert not [form_def for form_def in form_def_values if "contact_group_sales_ranges" in form_def.name]


@pytest.mark.django_db
def test_form_part_for_random_group(rf, admin_user):
    get_default_shop()
    group = get_default_customer_group()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    initialized_view = ContactGroupEditView(request=request, kwargs={"pk": group.pk})
    initialized_view.object = initialized_view.get_object()  # Just for test
    form_def_values = initialized_view.get_form().form_defs.values()
    assert [form_def for form_def in form_def_values if form_def.name == "base"]
    # contact_group_sales_ranges should be in form defs
    assert [form_def for form_def in form_def_values if "contact_group_sales_ranges" in form_def.name]


def get_edit_view_data(shop, group, min_value, max_value):
    prefix = "%d-%s" % (shop.pk, "contact_group_sales_ranges")
    min_value_field_name = "%s-min_value" % prefix
    max_value_field_name = "%s-max_value" % prefix
    return {
        "base-name__en": group.name,
        "base-price_display_mode": "none",
        min_value_field_name: min_value,
        max_value_field_name: max_value,
    }


@pytest.mark.django_db
def test_editing_sales_ranges(rf, admin_user):
    shop = get_default_shop()
    group = get_default_customer_group()
    data = get_edit_view_data(shop, group, 1, 100)
    assert ContactGroupSalesRange.objects.count() == 0
    # To make this test work we need to mock members form_part since the
    # extra forms does not render correctly
    with patch.object(ContactGroupEditView, "base_form_part_classes", [ContactGroupBaseFormPart]):
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        view = ContactGroupEditView.as_view()
        response = view(request=request, pk=group.pk)
        if hasattr(response, "render"):
            response.render()
        assert response.status_code in [200, 302]

    sales_range = ContactGroupSalesRange.objects.filter(group=group, shop=shop).first()
    assert sales_range.min_value == 1
    assert sales_range.max_value == 100


@pytest.mark.django_db
def test_editing_sales_ranges_multi_shop(rf, admin_user):
    default_shop = get_default_shop()
    another_shop = get_shop(prices_include_tax=True)
    another_shop.status = ShopStatus.ENABLED
    another_shop.save()
    group = get_default_customer_group()
    data = {}
    for shop in Shop.objects.all():
        data.update(get_edit_view_data(shop, group, 0, 50))

    assert ContactGroupSalesRange.objects.count() == 0
    # To make this test work we need to mock members form_part since the extra
    # forms does not render correctly
    with patch.object(ContactGroupEditView, "base_form_part_classes", [ContactGroupBaseFormPart]):
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        view = ContactGroupEditView.as_view()
        response = view(request=request, pk=group.pk)
        if hasattr(response, "render"):
            response.render()
        assert response.status_code in [200, 302]

    # Even if the data is for both shops only the current shop takes
    # effect. From admin sales ranges can be only defined for the current
    # shop.
    assert ContactGroupSalesRange.objects.count() == 1
    sales_range = ContactGroupSalesRange.objects.filter(group=group, shop=default_shop).first()
    assert sales_range.min_value == 0
    assert sales_range.max_value == 50
