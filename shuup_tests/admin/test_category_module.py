# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.db import transaction
from django.test import override_settings

from shuup.admin.modules.categories import CategoryModule
from shuup.admin.modules.categories.forms import (
    CategoryBaseForm, CategoryProductForm
)
from shuup.admin.modules.categories.views import (
    CategoryCopyVisibilityView, CategoryEditView
)
from shuup.core.models import (
    Category, CategoryStatus, CategoryVisibility,
    ShopProductVisibility
)
from shuup.testing.factories import (
    CategoryFactory, create_product, get_default_category,
    get_default_customer_group, get_default_shop
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import empty_iterable
from shuup_tests.utils.forms import get_form_data


@pytest.mark.django_db
def test_category_module_search(rf):
    cm = CategoryModule()
    category = CategoryFactory()
    request = rf.get("/")
    assert not empty_iterable(cm.get_search_results(request, query=category.identifier))
    assert empty_iterable(cm.get_search_results(request, query="k"))


@pytest.mark.django_db
def test_category_form_saving(rf):
    with transaction.atomic():
        category = CategoryFactory()
        form_kwargs = dict(instance=category, languages=("sw",), default_language="sw")
        form = CategoryBaseForm(**form_kwargs)
        assert isinstance(form, CategoryBaseForm)
        form_data = get_form_data(form, prepared=True)
        for lang, field_map in form.trans_name_map.items():
            for dst_field in field_map.values():
                form_data[form.add_prefix(dst_field)] = "IJWEHGWOHKSL"
        form_kwargs["data"] = form_data
        form = CategoryBaseForm(**form_kwargs)
        form.full_clean()
        form.save()
        category = form.instance
        category.set_current_language("sw")
        assert category.name == "IJWEHGWOHKSL"


@pytest.mark.django_db
def test_products_form_add():
    shop = get_default_shop()
    category = get_default_category()
    category.visibility = CategoryVisibility.VISIBLE_TO_LOGGED_IN
    category.status = CategoryStatus.INVISIBLE
    category.shops.add(shop)
    category.save()
    product = create_product("test_product", shop=shop)
    shop_product = product.get_shop_instance(shop)
    product_category = product.category
    assert (product_category is None)
    assert (category not in shop_product.categories.all())
    data = {
        "primary_products": ["%s" % product.id]
    }
    form = CategoryProductForm(shop=shop, category=category, data=data)
    form.full_clean()
    form.save()
    shop_product.refresh_from_db()
    product.refresh_from_db(())
    assert (shop_product.primary_category == category)
    assert (category in shop_product.categories.all())
    assert (shop_product.visibility_limit.value == category.visibility.value)
    assert (shop_product.visibility == ShopProductVisibility.NOT_VISIBLE)
    assert (product.category is None)


@pytest.mark.django_db
def test_products_form_update_default_category():
    shop = get_default_shop()
    category = get_default_category()
    category.shops.add(shop)
    product = create_product("test_product", shop=shop)
    shop_product = product.get_shop_instance(shop)
    product_category = product.category
    assert (product_category is None)
    assert (category not in shop_product.categories.all())
    data = {
        "primary_products": ["%s" % product.id],
        "update_product_category": True
    }
    form = CategoryProductForm(shop=shop, category=category, data=data)
    form.full_clean()
    form.save()
    shop_product.refresh_from_db()
    product.refresh_from_db()
    assert (shop_product.primary_category == category)
    assert (category in shop_product.categories.all())
    assert (product.category == category)


@pytest.mark.django_db
def test_products_form_add_multiple_products():
    shop = get_default_shop()
    category = get_default_category()
    category.shops.add(shop)
    product_ids = []
    for x in range(0, 15):
        product = create_product("%s" % x, shop=shop)
        product_ids.append(product.id)

    assert (category.shop_products.count() == 0)
    data = {
        "additional_products": ["%s" % product_id for product_id in product_ids]
    }
    form = CategoryProductForm(shop=shop, category=category, data=data)
    form.full_clean()
    form.save()

    category.refresh_from_db()
    assert (category.shop_products.count() == len(product_ids))


@pytest.mark.django_db
def test_products_form_remove():
    shop = get_default_shop()
    category = get_default_category()
    category.shops.add(shop)
    product = create_product("test_product", shop=shop)
    product.category = category
    product.save()
    shop_product = product.get_shop_instance(shop)
    shop_product.primary_category = category
    shop_product.save()
    shop_product.categories.add(category)

    product.refresh_from_db()
    assert (product.category == category)
    shop_product.refresh_from_db()
    assert (shop_product.primary_category == category)
    assert (shop_product.categories.count() == 1)
    assert (shop_product.categories.first() == category)

    data = {
        "remove_products": ["%s" % shop_product.id]
    }
    form = CategoryProductForm(shop=shop, category=category, data=data)
    form.full_clean()
    form.save()

    category.refresh_from_db()
    assert (category.shop_products.count() == 0)
    product.refresh_from_db()
    assert (product.category is None)
    shop_product.refresh_from_db()
    assert (shop_product.primary_category is None)
    assert (shop_product.categories.count() == 0)


@pytest.mark.django_db
def test_category_create(rf, admin_user):
    get_default_shop()
    with override_settings(LANGUAGES=[("en", "en")]):
        view = CategoryEditView.as_view()
        cat_name = "Random name"
        data = {
            "base-name__en": cat_name,
            "base-status": CategoryStatus.VISIBLE.value,
            "base-visibility": CategoryVisibility.VISIBLE_TO_ALL.value,
            "base-ordering": 1
        }
        assert Category.objects.count() == 0
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        response = view(request, pk=None)
        if hasattr(response, "render"):
            response.render()
        assert response.status_code in [200, 302]
        assert Category.objects.count() == 1
        assert Category.objects.first().name == cat_name


@pytest.mark.django_db
def test_category_copy_visibility(rf, admin_user):
    shop = get_default_shop()
    group = get_default_customer_group()
    category = get_default_category()
    category.status = CategoryStatus.INVISIBLE
    category.visibility = CategoryVisibility.VISIBLE_TO_GROUPS
    category.shops.add(shop)
    category.visibility_groups.add(group)
    category.save()
    product = create_product("test_product", shop=shop)
    shop_product = product.get_shop_instance(shop)
    shop_product.primary_category = category
    shop_product.save()
    view = CategoryCopyVisibilityView.as_view()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    response = view(request, pk=category.pk)
    shop_product.refresh_from_db()
    assert response.status_code == 200
    assert shop_product.visibility == ShopProductVisibility.NOT_VISIBLE
    assert shop_product.visibility_limit.value == category.visibility.value
    assert shop_product.visibility_groups.count() == category.visibility_groups.count()
    assert set(shop_product.visibility_groups.all()) == set(category.visibility_groups.all())
