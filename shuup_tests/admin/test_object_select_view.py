# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import json
import pytest
from django.test import override_settings
from django.utils.translation import activate, get_language

from shuup.admin.utils.permissions import set_permissions_for_group
from shuup.admin.views.select import ObjectSelectorView
from shuup.core.models import (
    Category,
    CategoryStatus,
    CompanyContact,
    PersonContact,
    Product,
    ProductMode,
    SalesUnit,
    ShopProduct,
    ShopProductVisibility,
    Supplier,
)
from shuup.testing.factories import (
    create_product,
    create_random_user,
    get_default_permission_group,
    get_default_shop,
    get_shop,
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils.fixtures import regular_user


def _get_object_selector_results(rf, view, model_name, search_str, user, search_mode=None, sales_units=None, shop=None):
    data = {"selector": model_name, "q": search_str}
    if search_mode:
        data.update({"searchMode": search_mode})

    if sales_units:
        data.update({"salesUnits": sales_units})

    if shop:
        data.update({"shop": shop.pk})

    request = apply_request_middleware(rf.get("sa/object-selector", data), user=user)
    response = view(request)
    assert response.status_code == 200
    return json.loads(response.content.decode("utf-8")).get("results")


@pytest.mark.django_db
def test_ajax_object_select_view_with_products(rf, admin_user):
    shop = get_default_shop()
    activate("en")
    view = ObjectSelectorView.as_view()

    # No products, no results
    results = _get_object_selector_results(rf, view, "shuup.product", "some str", admin_user)
    assert len(results) == 0

    product_name_en = "The Product"
    product = create_product("the product", shop=shop, **{"name": product_name_en})
    shop_product = product.get_shop_instance(shop)

    product_name_fi = "tuote"
    product.set_current_language("fi")
    # Making sure we are not getting duplicates from translations
    product.name = product_name_fi  # It seems that finnish translation overlaps with english name
    product.save()

    view = ObjectSelectorView.as_view()

    results = _get_object_selector_results(rf, view, "shuup.product", "some str", admin_user)
    assert len(results) == 0

    data = {"selector": "shuup.product", "q": ""}
    request = apply_request_middleware(rf.get("sa/object-selector", data), user=admin_user)
    response = view(request)
    assert response.status_code == 400

    results = _get_object_selector_results(rf, view, "shuup.product", "product", admin_user)
    assert len(results) == 1
    assert results[0].get("id") == product.id
    assert results[0].get("name") == product_name_en

    results = _get_object_selector_results(rf, view, "shuup.shopproduct", "product", admin_user)
    assert len(results) == 1
    assert results[0].get("id") == shop_product.id
    assert results[0].get("name") == product_name_en

    activate("fi")
    results = _get_object_selector_results(rf, view, "shuup.product", "product", admin_user)
    assert get_language() == "fi"
    assert len(results) == 1
    assert results[0].get("id") == product.id
    assert results[0].get("name") == product_name_fi

    results = _get_object_selector_results(rf, view, "shuup.product", "  product  ", admin_user)
    assert len(results) == 1
    assert results[0].get("id") == product.id
    assert results[0].get("name") == product_name_fi

    product.soft_delete()
    results = _get_object_selector_results(rf, view, "shuup.product", "product", admin_user)
    assert len(results) == 0
    supplier1 = Supplier.objects.create(name="supplier1", enabled=True)
    supplier1.shops.add(shop)
    product = create_product(
        "test-product", shop, default_price="200", supplier=supplier1, mode=ProductMode.SIMPLE_VARIATION_PARENT
    )
    results = _get_object_selector_results(rf, view, "shuup.product", "  product  ", admin_user, "parent_product")
    assert len(results) == 1

    shop2 = get_shop(identifier="shop2")
    supplier2 = Supplier.objects.create(name="supplier2", enabled=False)
    supplier2.shops.add(shop2)
    product2 = create_product(
        "test-product-two", shop2, default_price="200", supplier=supplier2, mode=ProductMode.SIMPLE_VARIATION_PARENT
    )
    results = _get_object_selector_results(rf, view, "shuup.product", "  product  ", admin_user, "parent_product")
    assert len(results) == 1


@pytest.mark.django_db
def test_multi_object_select_with_main_products(rf, admin_user):
    shop = get_default_shop()
    activate("en")
    view = ObjectSelectorView.as_view()

    var1 = "size"
    var2 = "color"
    parent = create_product("test", shop=shop, **{"name": "test"})
    for a in range(4):
        for b in range(3):
            product_name = "test-%s-%s" % (a, b)
            child = create_product(product_name, shop=shop, **{"name": product_name})
            child.link_to_parent(parent, variables={var1: a, var2: b})
            assert child.mode == ProductMode.VARIATION_CHILD

    assert parent.variation_children.count() == 4 * 3
    assert Product.objects.count() == 4 * 3 + 1

    results = _get_object_selector_results(rf, view, "shuup.product", "test", admin_user)
    assert len(results) == Product.objects.count()

    results = _get_object_selector_results(rf, view, "shuup.product", "test", admin_user, "main")
    assert len(results) == 1

    create_product("test1", shop=shop, **{"name": "test 123"})
    results = _get_object_selector_results(rf, view, "shuup.product", "test", admin_user, "main")
    assert len(results) == 2

    create_product("2", shop=shop, **{"name": "something that doesn not match with the search term"})
    results = _get_object_selector_results(rf, view, "shuup.product", "test", admin_user, "main")
    assert len(results) == 2


@pytest.mark.django_db
def test_multi_object_select_with_sellable_only_products(rf, admin_user):
    shop = get_default_shop()
    activate("en")
    view = ObjectSelectorView.as_view()

    var1 = "size"
    var2 = "color"
    parent = create_product("test", shop=shop, **{"name": "test"})
    for a in range(4):
        for b in range(3):
            product_name = "test-%s-%s" % (a, b)
            child = create_product(product_name, shop=shop, **{"name": product_name})
            child.link_to_parent(parent, variables={var1: a, var2: b})
            assert child.mode == ProductMode.VARIATION_CHILD

    assert parent.variation_children.count() == 4 * 3
    assert Product.objects.count() == 4 * 3 + 1

    results = _get_object_selector_results(rf, view, "shuup.product", "test", admin_user)
    assert len(results) == Product.objects.count()

    results = _get_object_selector_results(rf, view, "shuup.product", "test", admin_user, "sellable_mode_only")
    assert len(results) == Product.objects.count() - 1

    create_product("test1", shop=shop, **{"name": "test 123"})
    results = _get_object_selector_results(rf, view, "shuup.product", "test", admin_user, "sellable_mode_only")
    assert len(results) == Product.objects.count() - 1  # Still only the parent is excluded
    assert Product.objects.count() == 4 * 3 + 2

    # hide all shop products
    ShopProduct.objects.all().update(visibility=ShopProductVisibility.NOT_VISIBLE)
    results = _get_object_selector_results(rf, view, "shuup.product", "test", admin_user, "sellable_mode_only")
    assert len(results) == 0

    # show them again
    ShopProduct.objects.all().update(visibility=ShopProductVisibility.ALWAYS_VISIBLE)
    results = _get_object_selector_results(rf, view, "shuup.product", "test", admin_user, "sellable_mode_only")
    assert len(results) == Product.objects.count() - 1

    # delete all products
    [product.soft_delete() for product in Product.objects.all()]
    results = _get_object_selector_results(rf, view, "shuup.product", "test", admin_user, "sellable_mode_only")
    assert len(results) == 0


@pytest.mark.django_db
def test_multi_object_select_with_product_sales_unit(rf, admin_user):
    shop = get_default_shop()
    activate("en")
    gram = SalesUnit.objects.create(symbol="g", name="Grams")
    create_product("gram", shop=shop, **{"name": "Gram Product", "sales_unit": gram})

    pieces = SalesUnit.objects.create(symbol="pcs", name="Pieces")
    create_product("pcs", shop=shop, **{"name": "Pieces Product", "sales_unit": pieces})

    kg = SalesUnit.objects.create(symbol="kg", name="Kilograms")
    create_product("kg", shop=shop, **{"name": "Kilogram Product", "sales_unit": kg})

    oz = SalesUnit.objects.create(symbol="oz", name="Ounce")
    create_product("oz", shop=shop, **{"name": "Ounce Product", "sales_unit": oz})

    view = ObjectSelectorView.as_view()

    results = _get_object_selector_results(rf, view, "shuup.product", "Product", admin_user)
    assert len(results) == 4

    assert len(_get_object_selector_results(rf, view, "shuup.product", "Product", admin_user, sales_units="g")) == 1
    assert len(_get_object_selector_results(rf, view, "shuup.product", "Product", admin_user, sales_units="pcs")) == 1
    assert len(_get_object_selector_results(rf, view, "shuup.product", "Product", admin_user, sales_units="kg")) == 1
    assert len(_get_object_selector_results(rf, view, "shuup.product", "Product", admin_user, sales_units="oz")) == 1

    assert len(_get_object_selector_results(rf, view, "shuup.product", "Product", admin_user, sales_units="g,oz")) == 2
    assert (
        len(_get_object_selector_results(rf, view, "shuup.product", "Product", admin_user, sales_units="g,kg,pcs")) == 3
    )
    assert (
        len(_get_object_selector_results(rf, view, "shuup.product", "Product", admin_user, sales_units="oz,pcs,g,kg"))
        == 4
    )


@pytest.mark.django_db
@pytest.mark.parametrize("contact_cls", [PersonContact, CompanyContact])
def test_ajax_object_select_view_with_contacts(rf, contact_cls, admin_user):
    shop = get_default_shop()
    view = ObjectSelectorView.as_view()

    data = {"selector": "", "q": "some str"}
    request = apply_request_middleware(rf.get("sa/object-selector", data), user=admin_user)
    response = view(request)
    assert response.status_code == 400

    model_name = "shuup.%s" % contact_cls._meta.model_name
    results = _get_object_selector_results(rf, view, model_name, "some str", admin_user)
    assert len(results) == 0

    # # customer doesn't belong to shop
    customer = contact_cls.objects.create(name="Michael Jackson", email="michael@example.com")
    results = _get_object_selector_results(rf, view, model_name, "michael", admin_user)
    assert len(results) == 0

    customer.add_to_shop(shop)
    results = _get_object_selector_results(rf, view, model_name, "michael", admin_user)
    assert len(results) == 1
    assert results[0].get("id") == customer.id
    assert results[0].get("name") == customer.name

    results = _get_object_selector_results(rf, view, model_name, "jacks", admin_user)
    assert len(results) == 1
    assert results[0].get("id") == customer.id
    assert results[0].get("name") == customer.name

    results = _get_object_selector_results(rf, view, model_name, "el@ex", admin_user)
    assert len(results) == 1
    assert results[0].get("id") == customer.id
    assert results[0].get("name") == customer.name

    results = _get_object_selector_results(
        rf, view, model_name, "random", admin_user
    )  # Shouldn't find anything with this
    assert len(results) == 0


@pytest.mark.django_db
@pytest.mark.parametrize("contact_cls", [PersonContact, CompanyContact])
def test_ajax_object_select_view_with_contacts_multipleshop(rf, contact_cls):
    shop1 = get_default_shop()
    shop2 = get_shop(identifier="shop2")
    staff = create_random_user(is_staff=True)
    shop1.staff_members.add(staff)
    shop2.staff_members.add(staff)

    view = ObjectSelectorView.as_view()
    model_name = "shuup.%s" % contact_cls._meta.model_name

    customer = contact_cls.objects.create(name="Michael Jackson", email="michael@example.com")
    customer_shop1 = contact_cls.objects.create(name="Roberto", email="robert@example.com")
    customer_shop2 = contact_cls.objects.create(name="Maria", email="maria@example.com")

    permission_group = get_default_permission_group()
    staff.groups.add(permission_group)
    permission_name = "%s.object_selector" % contact_cls._meta.model_name
    set_permissions_for_group(permission_group, [permission_name])

    results = _get_object_selector_results(rf, view, model_name, "michael", staff)
    assert len(results) == 0

    customer.add_to_shop(shop1)
    customer.add_to_shop(shop2)
    customer_shop1.add_to_shop(shop1)
    customer_shop2.add_to_shop(shop2)

    for shop in [shop1, shop2]:
        results = _get_object_selector_results(rf, view, model_name, "michael", staff, shop=shop)
        assert len(results) == 1
        assert results[0].get("id") == customer.id
        assert results[0].get("name") == customer.name

        results = _get_object_selector_results(rf, view, model_name, "roberto", staff, shop=shop)
        if shop == shop1:
            assert len(results) == 1
            assert results[0].get("id") == customer_shop1.id
            assert results[0].get("name") == customer_shop1.name
        else:
            assert len(results) == 0

        results = _get_object_selector_results(rf, view, model_name, "maria", staff, shop=shop)
        if shop == shop2:
            assert len(results) == 1
            assert results[0].get("id") == customer_shop2.id
            assert results[0].get("name") == customer_shop2.name
        else:
            assert len(results) == 0


@pytest.mark.django_db
def test_ajax_object_select_view_with_categories(rf, admin_user):
    activate("en")
    shop = get_default_shop()
    view = ObjectSelectorView.as_view()

    # No categories, no results
    results = _get_object_selector_results(rf, view, "shuup.category", "some str", admin_user)
    assert len(results) == 0

    category = Category.objects.create(
        parent=None,
        identifier="test",
        name="test",
    )
    category.shops.add(shop)

    results = _get_object_selector_results(rf, view, "shuup.category", "some str", admin_user)
    assert len(results) == 0

    results = _get_object_selector_results(rf, view, "shuup.category", category.name, admin_user)
    assert len(results) == 1

    category.soft_delete()
    results = _get_object_selector_results(rf, view, "shuup.category", category.name, admin_user)
    assert len(results) == 0


@pytest.mark.django_db
def test_object_multiselect_inactive_users_and_contacts(rf, regular_user, admin_user):
    """
    Make sure inactive users and contacts are filtered from search results.
    """
    shop = get_default_shop()
    view = ObjectSelectorView.as_view()
    assert "joe" in regular_user.username

    results = _get_object_selector_results(rf, view, "auth.user", "joe", admin_user)
    assert len(results) == 1
    assert results[0].get("id") == regular_user.id
    assert results[0].get("name") == regular_user.username

    contact = PersonContact.objects.create(first_name="Joe", last_name="Somebody")

    # contact not in shop
    results = _get_object_selector_results(rf, view, "shuup.personcontact", "joe", admin_user)
    assert len(results) == 0

    contact.add_to_shop(shop)
    results = _get_object_selector_results(rf, view, "shuup.personcontact", "joe", admin_user)
    assert len(results) == 1

    assert results[0].get("id") == contact.id
    assert results[0].get("name") == contact.name

    contact.is_active = False
    contact.save()

    results = _get_object_selector_results(rf, view, "shuup.personcontact", "joe", admin_user)

    assert len(results) == 0


@pytest.mark.django_db
def test_object_select_category(rf, admin_user):
    shop = get_default_shop()
    activate("en")
    view = ObjectSelectorView.as_view()

    category1 = Category.objects.create(name="category", status=CategoryStatus.VISIBLE)
    category2 = Category.objects.create(name="category", status=CategoryStatus.INVISIBLE)
    Category.objects.create(name="category")
    category1.shops.add(shop)
    category2.shops.add(shop)

    results = _get_object_selector_results(rf, view, "shuup.category", "category", admin_user)
    assert len(results) == 2

    # only visible
    results = _get_object_selector_results(rf, view, "shuup.category", "category", admin_user, search_mode="visible")
    assert len(results) == 1


@pytest.mark.django_db
def test_object_select_supplier(rf, admin_user):
    shop = get_default_shop()
    activate("en")
    view = ObjectSelectorView.as_view()

    supplier1 = Supplier.objects.create(name="supplier1", enabled=True)
    supplier2 = Supplier.objects.create(name="supplier2", enabled=False)
    Supplier.objects.create(name="supplier3", enabled=True)

    supplier1.shops.add(shop)
    supplier2.shops.add(shop)

    results = _get_object_selector_results(rf, view, "shuup.supplier", "supplier", admin_user)
    assert len(results) == 2

    # only enabled
    results = _get_object_selector_results(rf, view, "shuup.supplier", "supplier", admin_user, search_mode="enabled")
    assert len(results) == 1


@pytest.mark.django_db
def test_object_shop_products_with_supplier_filter(rf, admin_user):
    shop = get_default_shop()
    activate("en")
    view = ObjectSelectorView.as_view()

    superuser1 = create_random_user(is_superuser=True, is_staff=True)
    supplier1 = Supplier.objects.create(identifier=superuser1.username)
    superuser2 = create_random_user(is_superuser=True, is_staff=True)
    supplier2 = Supplier.objects.create(identifier=superuser2.username)

    product_name_en = "ok"
    product = create_product("test1", shop=shop, supplier=supplier1, **{"name": product_name_en})
    shop_product = product.get_shop_instance(shop)
    assert shop_product.suppliers.filter(pk=supplier1.pk).exists()
    supplier_provider = "shuup.testing.supplier_provider.UsernameSupplierProvider"
    with override_settings(SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC=supplier_provider):
        results = _get_object_selector_results(rf, view, "shuup.shopproduct", "ok", superuser1)
        assert len(results) == 1
        assert results[0].get("id") == shop_product.id
        assert results[0].get("name") == product_name_en

        results = _get_object_selector_results(rf, view, "shuup.shopproduct", "ok", superuser2)
        assert len(results) == 0
