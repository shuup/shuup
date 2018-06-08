# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime

import pytest
from django.contrib.auth import get_user_model

from shuup.admin.modules.products.views import ProductListView
from shuup.admin.modules.settings.view_settings import ViewSettings
from shuup.admin.utils.picotable import (
    ChoicesFilter, Column, DateRangeFilter, Filter, MPTTFilter,
    MultiFieldTextFilter, Picotable, RangeFilter, TextFilter
)
from shuup.apps.provides import override_provides
from shuup.core.models import Category, Product, ShopProduct
from shuup.testing.factories import get_default_shop
from shuup.testing.mock_population import populate_if_required
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import empty_iterable
from shuup_tests.utils.fixtures import regular_user


class PicoContext(object):
    def __init__(self, request):
        self.request = request

    def superuser_display(self, instance):  # Test indirect `display` callable
        return "very super" if instance.is_superuser else "-"


class CustomProductDataColumn(object):
    def get_custom_product_info_display(self, shop_product):
        return "product-data-%d" % shop_product.pk

    def get_column(self, model, known_names, identifier):
        return Column("custom_product_info", u"CustomProductInfo", display="get_custom_product_info_display")


def instance_id(instance):  # Test direct `display` callable
    return instance.id

def false_and_true():
    return [(False, "False"), (True, "True")]

def get_pico(rf, model=None, columns=None):
    get_default_shop()
    model = model or get_user_model()
    columns = columns or [
        Column("id", "Id", filter_config=Filter(), display=instance_id),
        Column("username", "Username", sortable=False, filter_config=MultiFieldTextFilter(filter_fields=("username", "email"), operator="iregex")),
        Column("email", "Email", sortable=False, filter_config=TextFilter()),
        Column("is_superuser", "Is Superuser", display="superuser_display", filter_config=ChoicesFilter(choices=false_and_true())),
        Column("is_active", "Is Active", filter_config=ChoicesFilter(choices=false_and_true)),  # `choices` callable
        Column("date_joined", "Date Joined", filter_config=DateRangeFilter())
    ]

    request = apply_request_middleware(rf.get("/"))
    return Picotable(
        request=request,
        columns=columns,
        mass_actions=[],
        queryset=model.objects.all(),
        context=PicoContext(request)
    )


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_picotable_basic(rf, admin_user, regular_user):
    pico = get_pico(rf)
    data = pico.get_data({"perPage": 100, "page": 1})
    assert len(data["items"]) == get_user_model().objects.count()


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_picotable_display(rf, admin_user, regular_user):
    pico = get_pico(rf)
    data = pico.get_data({"perPage": 100, "page": 1})
    for item in data["items"]:
        if item["id"] == admin_user.pk:
            assert item["is_superuser"] == "very super"
        if item["id"] == regular_user.pk:
            assert item["is_superuser"] == "-"


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_picotable_default_sort(rf, admin_user, regular_user):
    pico = get_pico(rf)
    data = pico.get_data({"perPage": 100, "page": 1})
    id = None
    for item in data["items"]:
        if id is not None:
            assert item["id"] <= id, "sorting does not work"
        id = item["id"]


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_picotable_sort(rf, admin_user, regular_user):
    pico = get_pico(rf)
    data = pico.get_data({"perPage": 100, "page": 1, "sort": "-id"})
    id = None
    for item in data["items"]:
        if id is not None:
            assert item["id"] <= id, "sorting does not work"
        id = item["id"]


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_picotable_invalid_sort(rf, admin_user, regular_user):
    pico = get_pico(rf)
    with pytest.raises(ValueError):
        data = pico.get_data({"perPage": 100, "page": 1, "sort": "-email"})


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_picotable_choice_filter(rf, admin_user, regular_user):
    pico = get_pico(rf)
    data = pico.get_data({"perPage": 100, "page": 1, "filters": {"is_superuser": True}})
    assert len(data["items"]) == get_user_model().objects.filter(is_superuser=True).count()


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_picotable_text_filter(rf, admin_user, regular_user):
    pico = get_pico(rf)
    data = pico.get_data({"perPage": 100, "page": 1, "filters": {"email": admin_user.email}})
    assert len(data["items"]) == get_user_model().objects.filter(is_superuser=True).count()


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_picotable_multi_filter(rf, admin_user, regular_user):
    pico = get_pico(rf)
    data = pico.get_data({"perPage": 100, "page": 1, "filters": {"username": "."}})
    assert len(data["items"]) == get_user_model().objects.count()


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_picotable_range_filter(rf, regular_user):
    pico = get_pico(rf)
    one_day = datetime.timedelta(days=1)
    assert not empty_iterable(pico.get_data({"perPage": 100, "page": 1, "filters": {"date_joined": {"min": regular_user.date_joined - one_day}}})["items"])
    assert not empty_iterable(pico.get_data({"perPage": 100, "page": 1, "filters": {"date_joined": {"max": regular_user.date_joined + one_day}}})["items"])
    # TODO: a false test for this

def test_column_is_user_friendly():
    with pytest.raises(NameError):
        Column(id="foo", title="bar", asdf=True)

@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_picotable_no_mobile_link_for_missing_object_url(rf, admin_user, regular_user):
    pico = get_pico(rf)
    pico.get_object_url = lambda object: "http://www.fakeurl.com"
    data = pico.get_data({"perPage": 100, "page": 1})
    assert data["items"][0]["_linked_in_mobile"]

    pico.get_object_url = None
    data = pico.get_data({"perPage": 100, "page": 1})
    assert not data["items"][0]["_linked_in_mobile"]


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_choice_filter_with_default(rf, admin_user, regular_user):
    columns = [
        Column("id", "Id", filter_config=Filter(), display=instance_id),
        Column("username", "Username", sortable=False, filter_config=MultiFieldTextFilter(filter_fields=("username", "email"), operator="iregex")),
        Column("email", "Email", sortable=False, filter_config=TextFilter()),
        Column("is_superuser", "Is Superuser", display="superuser_display", filter_config=ChoicesFilter(choices=false_and_true())),
        Column("date_joined", "Date Joined", filter_config=DateRangeFilter())
    ]

    is_active = [Column("is_active", "Is Active", filter_config=ChoicesFilter(choices=false_and_true))]
    is_active_with_default = [Column("is_active", "Is Active", filter_config=ChoicesFilter(choices=false_and_true, default=True))]

    query = {"perPage": 100, "page": 1, "sort": "+id"}

    pico_no_defaults = get_pico(rf, columns=(columns + is_active))
    data = pico_no_defaults.get_data(query)

    superuser_field = data["columns"][3]
    assert superuser_field["id"] == "is_superuser"
    assert len(superuser_field["filter"]["choices"]) == 3
    assert superuser_field["filter"]["defaultChoice"] == "_all"
    assert superuser_field["filter"]["choices"][0][0] == superuser_field["filter"]["defaultChoice"]

    user_data = data["items"][0]
    user = get_user_model().objects.get(id=user_data["id"])
    assert user.is_active

    pico_with_defaults = get_pico(rf, columns=(columns + is_active_with_default))
    data = pico_with_defaults.get_data(query)
    user_data = data["items"][0]
    user_with_defaults = get_user_model().objects.get(id=user_data["id"])
    assert user_with_defaults == user

    user.is_active = False
    user.save()

    data = pico_no_defaults.get_data(query)
    user_data = data["items"][0]
    new_user = get_user_model().objects.get(id=user_data["id"])
    assert new_user == user

    data = pico_with_defaults.get_data(query)
    user_data = data["items"][0]
    new_user_with_defaults = get_user_model().objects.get(id=user_data["id"])
    assert new_user_with_defaults != user_with_defaults


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_picotable_correctly_sorts_translated_fields(rf, admin_user, regular_user):
    """
    Make sure that translated fields, such as product names, are correctly sorted
    """
    populate_if_required()

    columns = [
        Column("id", "Id", filter_config=Filter(), display=instance_id),
        Column(
            "name", "Name", sort_field="translations__name",
            filter_config=TextFilter(filter_field="translations__name")),
    ]

    pico = get_pico(rf, model=Product, columns=columns)

    # Verify ascending sort
    sorted_products = pico.get_data({"perPage": 100, "page": 1, "sort": "+name"})
    sorted_names = [p["name"] for p in sorted_products["items"]]
    assert sorted_names == sorted(sorted_names)

    # Verify descending sort
    sorted_products = pico.get_data({"perPage": 100, "page": 1, "sort": "-name"})
    sorted_names = [p["name"] for p in sorted_products["items"]]
    assert sorted_names == sorted(sorted_names, reverse=True)


@pytest.mark.django_db
def test_mptt_filter(rf):
    parent_category = Category.objects.create(name="parent")
    child_category = Category.objects.create(name="child")
    parent_category.children.add(child_category)
    columns = [
        Column(
            "name", "name",
            filter_config=MPTTFilter(
                choices=Category.objects.all(),
                filter_field="id"
            )
        )
    ]
    pico = get_pico(rf, model=Category, columns=columns)
    data = pico.get_data({"perPage": 100, "page": 1, "filters": {"id": parent_category.id}})
    assert len(data["items"]) == 2

    data = pico.get_data({"perPage": 100, "page": 1, "filters": {"name": child_category.id}})
    assert len(data["items"]) == 1


@pytest.mark.django_db
def test_provide_columns():
    with override_provides("provided_columns_ShopProduct", [
            "shuup_tests.admin.test_picotable:CustomProductDataColumn"]):
        view_settings = ViewSettings(ShopProduct, ProductListView.default_columns, ProductListView)
        column_ids = [col.id for col in view_settings.inactive_columns]  # provided column is not set active yet
        assert "custom_product_info" in column_ids
