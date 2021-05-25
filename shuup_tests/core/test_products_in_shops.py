# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings
from django.utils.timezone import now
from parler.models import TranslationDoesNotExist

from shuup import configuration
from shuup.core.excs import ProductNotOrderableProblem, ProductNotVisibleProblem
from shuup.core.models import (
    AnonymousContact,
    Category,
    ProductMode,
    ProductVariationResult,
    ProductVariationVariable,
    ProductVariationVariableValue,
    ProductVisibility,
    ShopProduct,
    ShopProductVisibility,
    Supplier,
    get_person_contact,
)
from shuup.testing.factories import (
    CategoryFactory,
    create_product,
    get_all_seeing_key,
    get_default_customer_group,
    get_default_product,
    get_default_shop,
    get_default_shop_product,
    get_default_supplier,
)
from shuup_tests.core.utils import modify
from shuup_tests.utils import error_does_not_exist, error_exists, printable_gibberish
from shuup_tests.utils.fixtures import regular_user


@pytest.mark.django_db
def test_image_inheritance():
    shop = get_default_shop()
    product = get_default_product()
    shop_product = product.get_shop_instance(shop)
    assert product.primary_image_id
    assert shop_product.primary_image == product.primary_image


@pytest.mark.django_db
def test_product_orderability():
    anon_contact = AnonymousContact()
    shop_product = get_default_shop_product()
    supplier = get_default_supplier(shop_product.shop)

    with modify(shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_ALL, orderable=True):
        shop_product.raise_if_not_orderable(supplier=supplier, customer=anon_contact, quantity=1)
        assert shop_product.is_orderable(supplier=supplier, customer=anon_contact, quantity=1, allow_cache=False)

    with modify(shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_LOGGED_IN, orderable=True):
        with pytest.raises(ProductNotOrderableProblem):
            shop_product.raise_if_not_orderable(supplier=supplier, customer=anon_contact, quantity=1)
        assert not shop_product.is_orderable(supplier=supplier, customer=anon_contact, quantity=1, allow_cache=False)


@pytest.mark.django_db
def test_purchasability():
    anon_contact = AnonymousContact()
    shop_product = get_default_shop_product()
    supplier = get_default_supplier(shop_product.shop)
    assert shop_product.purchasable

    shop_product.raise_if_not_orderable(supplier=supplier, customer=anon_contact, quantity=1)
    assert shop_product.is_orderable(supplier=supplier, customer=anon_contact, quantity=1, allow_cache=False)

    with modify(shop_product, purchasable=False):
        with pytest.raises(ProductNotOrderableProblem):
            shop_product.raise_if_not_orderable(supplier=supplier, customer=anon_contact, quantity=1)
        assert not shop_product.is_orderable(supplier=supplier, customer=anon_contact, quantity=1, allow_cache=False)


@pytest.mark.django_db
def test_product_minimum_order_quantity(admin_user):
    shop_product = get_default_shop_product()
    supplier = get_default_supplier(shop_product.shop)
    admin_contact = get_person_contact(admin_user)

    with modify(
        shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_ALL, orderable=True, minimum_purchase_quantity=10
    ):
        assert any(
            ve.code == "purchase_quantity_not_met"
            for ve in shop_product.get_orderability_errors(supplier=supplier, customer=admin_contact, quantity=1)
        )
        assert not any(
            ve.code == "purchase_quantity_not_met"
            for ve in shop_product.get_orderability_errors(supplier=supplier, customer=admin_contact, quantity=15)
        )


@pytest.mark.django_db
def test_product_order_multiple(admin_user):
    shop_product = get_default_shop_product()
    supplier = get_default_supplier(shop_product.shop)
    admin_contact = get_person_contact(admin_user)

    with modify(shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_ALL, orderable=True, purchase_multiple=7):
        assert any(
            ve.code == "invalid_purchase_multiple"
            for ve in shop_product.get_orderability_errors(supplier=supplier, customer=admin_contact, quantity=4)
        )
        assert any(
            ve.code == "invalid_purchase_multiple"
            for ve in shop_product.get_orderability_errors(supplier=supplier, customer=admin_contact, quantity=25)
        )
        assert not any(
            ve.code == "invalid_purchase_multiple"
            for ve in shop_product.get_orderability_errors(supplier=supplier, customer=admin_contact, quantity=49)
        )


@pytest.mark.django_db
def test_product_unsupplied(admin_user):
    shop_product = get_default_shop_product()
    fake_supplier = Supplier.objects.create(identifier="fake")
    fake_supplier.shops.add(shop_product.shop)
    admin_contact = get_person_contact(admin_user)

    with modify(shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_ALL, orderable=True):
        assert any(
            ve.code == "invalid_supplier"
            for ve in shop_product.get_orderability_errors(supplier=fake_supplier, customer=admin_contact, quantity=1)
        )


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_product_visibility(rf, admin_user, regular_user):
    anon_contact = get_person_contact(AnonymousUser())
    shop_product = get_default_shop_product()
    admin_contact = get_person_contact(admin_user)
    regular_contact = get_person_contact(regular_user)

    configuration.set(None, get_all_seeing_key(admin_contact), True)

    with modify(
        shop_product.product, deleted=True
    ):  # NB: assigning to `product` here works because `get_shop_instance` populates `_product_cache`
        assert error_exists(shop_product.get_visibility_errors(customer=anon_contact), "product_deleted")
        assert error_exists(shop_product.get_visibility_errors(customer=admin_contact), "product_deleted")
        with pytest.raises(ProductNotVisibleProblem):
            shop_product.raise_if_not_visible(anon_contact)
        assert not shop_product.is_list_visible()

    with modify(
        shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_ALL, visibility=ShopProductVisibility.NOT_VISIBLE
    ):
        assert error_exists(shop_product.get_visibility_errors(customer=anon_contact), "product_not_visible")
        assert error_does_not_exist(shop_product.get_visibility_errors(customer=admin_contact), "product_not_visible")
        assert not shop_product.is_list_visible()

    with modify(
        shop_product,
        visibility_limit=ProductVisibility.VISIBLE_TO_LOGGED_IN,
        visibility=ShopProductVisibility.ALWAYS_VISIBLE,
    ):
        assert error_exists(
            shop_product.get_visibility_errors(customer=anon_contact), "product_not_visible_to_anonymous"
        )
        assert error_does_not_exist(
            shop_product.get_visibility_errors(customer=admin_contact), "product_not_visible_to_anonymous"
        )

    customer_group = get_default_customer_group()
    grouped_user = get_user_model().objects.create_user(username=printable_gibberish(20))
    grouped_contact = get_person_contact(grouped_user)
    with modify(
        shop_product,
        visibility_limit=ProductVisibility.VISIBLE_TO_GROUPS,
        visibility=ShopProductVisibility.ALWAYS_VISIBLE,
    ):
        shop_product.visibility_groups.add(customer_group)
        customer_group.members.add(grouped_contact)
        customer_group.members.remove(get_person_contact(regular_user))
        assert error_does_not_exist(
            shop_product.get_visibility_errors(customer=grouped_contact), "product_not_visible_to_group"
        )
        assert error_does_not_exist(
            shop_product.get_visibility_errors(customer=admin_contact), "product_not_visible_to_group"
        )
        assert error_exists(
            shop_product.get_visibility_errors(customer=regular_contact), "product_not_visible_to_group"
        )

    configuration.set(None, get_all_seeing_key(admin_contact), False)


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_product_visibility_available_until(rf, admin_user, regular_user):
    anon_contact = get_person_contact(AnonymousUser())
    shop_product = get_default_shop_product()
    admin_contact = get_person_contact(admin_user)
    regular_contact = get_person_contact(regular_user)
    customer_group = get_default_customer_group()
    grouped_user = get_user_model().objects.create_user(username=printable_gibberish(20))
    grouped_contact = get_person_contact(grouped_user)
    customer_group.members.add(grouped_contact)

    with modify(shop_product, available_until=(now() + timedelta(seconds=200))):
        assert error_does_not_exist(shop_product.get_visibility_errors(customer=anon_contact), "product_not_available")
        assert error_does_not_exist(
            shop_product.get_visibility_errors(customer=grouped_contact), "product_not_available"
        )
        assert error_does_not_exist(shop_product.get_visibility_errors(customer=admin_contact), "product_not_available")
        assert error_does_not_exist(
            shop_product.get_visibility_errors(customer=regular_contact), "product_not_available"
        )

    with modify(shop_product, available_until=(now() - timedelta(seconds=150))):
        assert error_exists(shop_product.get_visibility_errors(customer=anon_contact), "product_not_available")
        assert error_exists(shop_product.get_visibility_errors(customer=grouped_contact), "product_not_available")
        assert error_exists(shop_product.get_visibility_errors(customer=admin_contact), "product_not_available")
        assert error_exists(shop_product.get_visibility_errors(customer=regular_contact), "product_not_available")


@pytest.mark.django_db
def test_complex_orderability(admin_user):
    shop = get_default_shop()

    fake_supplier = Supplier.objects.create(identifier="fake")
    fake_supplier.shops.add(shop)
    admin_contact = get_person_contact(admin_user)

    parent = create_product("SuperComplexVarParent")

    shop_product = ShopProduct.objects.create(
        product=parent, shop=shop, visibility=ShopProductVisibility.ALWAYS_VISIBLE
    )
    shop_product.suppliers.add(fake_supplier)
    shop_product.visibility = ShopProductVisibility.ALWAYS_VISIBLE
    shop_product.save()

    color_var = ProductVariationVariable.objects.create(product=parent, identifier="color")
    size_var = ProductVariationVariable.objects.create(product=parent, identifier="size")

    for color in ("yellow", "blue", "brown"):
        ProductVariationVariableValue.objects.create(variable=color_var, identifier=color)

    for size in ("small", "medium", "large", "huge"):
        ProductVariationVariableValue.objects.create(variable=size_var, identifier=size)

    combinations = list(parent.get_all_available_combinations())
    assert len(combinations) == (3 * 4)
    for combo in combinations:
        assert not combo["result_product_pk"]
        child = create_product("xyz-%s" % combo["sku_part"], shop=shop, supplier=fake_supplier)
        child.link_to_parent(parent, combo["variable_to_value"])
        result_product = ProductVariationResult.resolve(parent, combo["variable_to_value"])
        assert result_product == child

    assert parent.mode == ProductMode.VARIABLE_VARIATION_PARENT

    small_size_value = ProductVariationVariableValue.objects.get(variable=size_var, identifier="small")
    brown_color_value = ProductVariationVariableValue.objects.get(variable=color_var, identifier="brown")

    result1 = ProductVariationResult.resolve(parent, {color_var: brown_color_value, size_var: small_size_value})
    result2 = ProductVariationResult.resolve(
        parent, {color_var.pk: brown_color_value.pk, size_var.pk: small_size_value.pk}
    )
    assert result1 and result2
    assert result1.pk == result2.pk

    assert error_does_not_exist(
        shop_product.get_orderability_errors(supplier=fake_supplier, customer=admin_contact, quantity=1),
        code="no_sellable_children",
    )

    # result 1 is no longer sellable
    sp = result1.get_shop_instance(shop)
    sp.visibility = ShopProductVisibility.NOT_VISIBLE
    sp.save()

    assert error_does_not_exist(
        shop_product.get_orderability_errors(supplier=fake_supplier, customer=admin_contact, quantity=1),
        code="no_sellable_children",
    )

    # no sellable children
    for combo in combinations:
        result_product = ProductVariationResult.resolve(parent, combo["variable_to_value"])
        sp = result_product.get_shop_instance(shop)
        sp.visibility = ShopProductVisibility.NOT_VISIBLE
        sp.save()

    assert error_exists(
        shop_product.get_orderability_errors(supplier=fake_supplier, customer=admin_contact, quantity=1),
        code="no_sellable_children",
    )

    # no sellable children with no shop product
    for combo in combinations:
        result_product = ProductVariationResult.resolve(parent, combo["variable_to_value"])
        sp = result_product.get_shop_instance(shop)
        sp.delete()
        sp.save()

    assert error_exists(
        shop_product.get_orderability_errors(supplier=fake_supplier, customer=admin_contact, quantity=1),
        code="no_sellable_children",
    )


def test_simple_orderability(admin_user):
    shop = get_default_shop()
    fake_supplier = Supplier.objects.create(identifier="fake")
    fake_supplier.shops.add(shop)
    admin_contact = get_person_contact(admin_user)

    parent = create_product("SimpleVarParent", shop=shop, supplier=fake_supplier)
    children = [create_product("SimpleVarChild-%d" % x, shop=shop, supplier=fake_supplier) for x in range(10)]
    for child in children:
        child.link_to_parent(parent)
        sp = child.get_shop_instance(shop)
        # sp = ShopProduct.objects.create(
        #     shop=shop, product=child, visibility=ShopProductVisibility.ALWAYS_VISIBLE
        # )
        assert child.is_variation_child()
        assert not sp.is_list_visible()  # Variation children are not list visible

    assert parent.mode == ProductMode.SIMPLE_VARIATION_PARENT
    assert not list(parent.get_all_available_combinations())  # Simple variations can't have these.

    shop_product = parent.get_shop_instance(shop)
    assert error_does_not_exist(
        shop_product.get_orderability_errors(supplier=fake_supplier, customer=admin_contact, quantity=1),
        code="no_sellable_children",
    )

    first_child = children[0]
    child_sp = first_child.get_shop_instance(shop)
    child_sp.visibility = ShopProductVisibility.NOT_VISIBLE
    child_sp.save()

    assert error_does_not_exist(
        shop_product.get_orderability_errors(supplier=fake_supplier, customer=admin_contact, quantity=1),
        code="no_sellable_children",
    )

    for child in children:
        child_sp = child.get_shop_instance(shop)
        child_sp.visibility = ShopProductVisibility.NOT_VISIBLE
        child_sp.save()

    assert error_exists(
        shop_product.get_orderability_errors(supplier=fake_supplier, customer=admin_contact, quantity=1),
        code="no_sellable_children",
    )

    # delete all children shop products
    for child in children:
        child_sp = child.get_shop_instance(shop)
        child_sp.delete()

    assert error_exists(
        shop_product.get_orderability_errors(supplier=fake_supplier, customer=admin_contact, quantity=1),
        code="no_sellable_children",
    )


@pytest.mark.django_db
def test_product_categories(settings):
    with override_settings(SHUUP_AUTO_SHOP_PRODUCT_CATEGORIES=True):
        shop_product = get_default_shop_product()
        shop_product.categories.clear()
        shop_product.primary_category = None
        shop_product.save()

        assert not shop_product.primary_category
        assert not shop_product.categories.count()

        category_one = CategoryFactory()
        category_two = CategoryFactory()

        shop_product.categories.set(Category.objects.all())

        assert shop_product.primary_category  # this was automatically populated
        assert shop_product.primary_category.pk == category_one.pk  # it's the first one also

        shop_product.categories.clear()

        shop_product.primary_category = category_one
        shop_product.save()

        assert shop_product.primary_category == category_one
        assert category_one in shop_product.categories.all()

        # test removing
        shop_product.categories.remove(category_one)
        shop_product.refresh_from_db()
        assert not shop_product.categories.exists()

        shop_product.categories.add(category_one)
        category_one.soft_delete()
        assert not shop_product.categories.exists()

    with override_settings(SHUUP_AUTO_SHOP_PRODUCT_CATEGORIES=False):
        shop_product.categories.clear()
        shop_product.primary_category = None
        shop_product.save()

        assert not shop_product.primary_category
        assert not shop_product.categories.count()

        category_one = CategoryFactory()
        category_two = CategoryFactory()

        shop_product.categories.set(Category.objects.all())

        assert not shop_product.primary_category  # this was NOT automatically populated

        shop_product.categories.clear()

        shop_product.primary_category = category_one
        shop_product.save()

        assert shop_product.primary_category == category_one
        assert category_one not in shop_product.categories.all()


@pytest.mark.parametrize("key", ["name", "description", "short_description"])
@pytest.mark.django_db
def test_get_safe_strings(key):
    shop_product = get_default_shop_product()
    setattr(shop_product.product, key, "test")
    shop_product.product.save()
    shop_product.refresh_from_db()

    assert getattr(shop_product.product, key)
    with pytest.raises(TranslationDoesNotExist):
        getattr(shop_product, key)

    func = getattr(shop_product, "get_" + key)
    assert getattr(shop_product.product, key) == func()  # returns value from product

    # set value to shop_product
    new_value = "testing"
    setattr(shop_product, key, new_value)
    shop_product.save()
    shop_product.refresh_from_db()

    assert func() == new_value  # returns value from shop product


@pytest.mark.django_db
def test_shop_instance_cache():
    from shuup.core import cache

    cache.clear()

    shop = get_default_shop()
    product = create_product("product", shop)
    shop_product = product.get_shop_instance(shop)
    assert shop_product == product.get_shop_instance(shop)
