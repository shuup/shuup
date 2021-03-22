# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import override_settings

from shuup import configuration
from shuup.core.defaults.order_statuses import create_default_order_statuses
from shuup.core.excs import NoPaymentToCreateException
from shuup.core.models import Order, OrderLineType, Shop, get_person_contact
from shuup.core.order_creator import OrderCreator, OrderSource, SourceLine
from shuup.core.order_creator._creator import OrderProcessor
from shuup.core.order_creator.constants import ORDER_MIN_TOTAL_CONFIG_KEY
from shuup.core.pricing import TaxfulPrice
from shuup.testing.factories import (
    create_default_tax_rule,
    create_package_product,
    create_product,
    create_random_company,
    create_random_contact_group,
    create_random_person,
    create_random_user,
    get_address,
    get_default_customer_group,
    get_default_product,
    get_default_shop,
    get_default_supplier,
    get_initial_order_status,
    get_payment_method,
    get_shipping_method,
    get_shop,
    get_tax,
)
from shuup.utils.models import get_data_dict
from shuup.utils.money import Money
from shuup_tests.utils.basketish_order_source import BasketishOrderSource


def test_invalid_order_source_updating():
    with pytest.raises(ValueError):  # Test nonexisting key updating
        OrderSource(Shop()).update(__totes_not_here__=True)


def test_invalid_source_line_updating():
    source = OrderSource(Shop())
    with pytest.raises(TypeError):  # Test forbidden keys
        SourceLine(source).update({"update": True})


def test_codes_type_conversion():
    source = OrderSource(Shop())

    assert source.codes == []

    source.add_code("t")
    source.add_code("e")
    source.add_code("s")
    assert source.codes == ["t", "e", "s"]

    was_added = source.add_code("t")
    assert was_added is False
    assert source.codes == ["t", "e", "s"]

    was_cleared = source.clear_codes()
    assert was_cleared
    assert source.codes == []
    was_cleared = source.clear_codes()
    assert not was_cleared

    source.add_code("test")
    source.add_code(1)
    source.add_code("1")
    assert source.codes == ["test", "1"]


def seed_source(user, shop=None):
    source_shop = shop or get_default_shop()
    source = BasketishOrderSource(source_shop)
    billing_address = get_address()
    shipping_address = get_address(name="Shippy Doge")
    source.status = get_initial_order_status()
    source.billing_address = billing_address
    source.shipping_address = shipping_address
    source.customer = get_person_contact(user)
    source.payment_method = get_payment_method(shop)
    source.shipping_method = get_shipping_method(shop)
    assert source.payment_method_id == get_payment_method(shop).id
    assert source.shipping_method_id == get_shipping_method(shop).id
    return source


@pytest.mark.django_db
def test_order_creator(rf, admin_user):
    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(source.shop),
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    source.add_line(
        accounting_identifier="strawberries",
        type=OrderLineType.OTHER,
        quantity=1,
        base_unit_price=source.create_price(10),
        require_verification=True,
        extra={"runner": "runner"},
    )

    the_line = [sl for sl in source.get_lines() if sl.accounting_identifier == "strawberries"]
    assert the_line[0].data["extra"]["runner"] == "runner"

    creator = OrderCreator()
    order = creator.create_order(source)
    zero = Money(0, order.currency)

    taxful_total_price = TaxfulPrice(-50, order.currency)
    last_price = order.taxful_total_price
    order.taxful_total_price = taxful_total_price
    order.save()
    assert not order.is_paid()
    assert not order.is_canceled()
    assert not order.get_total_unpaid_amount() > zero
    assert order.get_total_unpaid_amount() == zero
    assert not order.get_total_unpaid_amount() < zero
    assert not order.can_create_payment()
    order.taxful_total_price = last_price
    order.save()

    assert not order.is_paid()
    assert not order.is_canceled()
    assert order.get_total_unpaid_amount() > zero
    assert not order.get_total_unpaid_amount() == zero
    assert not order.get_total_unpaid_amount() < zero
    assert order.can_create_payment()

    order.set_canceled()
    assert not order.is_paid()
    assert order.is_canceled()
    assert order.get_total_unpaid_amount() > zero
    assert not order.get_total_unpaid_amount() == zero
    assert not order.get_total_unpaid_amount() < zero
    assert not order.can_create_payment()

    order.create_payment(order.get_total_unpaid_amount())
    assert order.is_paid()
    assert order.is_canceled()
    assert not order.get_total_unpaid_amount() > zero
    assert order.get_total_unpaid_amount() == zero
    assert not order.get_total_unpaid_amount() < zero
    assert not order.can_create_payment()

    with pytest.raises(NoPaymentToCreateException):
        order.create_payment(order.get_total_unpaid_amount())
        order.create_payment(order.get_total_unpaid_amount() + Money(10, order.currency))
        order.create_payment(order.get_total_unpaid_amount() - Money(10, order.currency))

    assert get_data_dict(source.billing_address) == get_data_dict(order.billing_address)
    assert get_data_dict(source.shipping_address) == get_data_dict(order.shipping_address)
    customer = source.customer
    assert customer == order.customer
    assert customer.groups.count() == 1
    assert customer.groups.first() == order.customer_groups.first()
    assert customer.tax_group is not None
    assert customer.tax_group == order.tax_group

    assert source.payment_method == order.payment_method
    assert source.shipping_method == order.shipping_method
    assert order.pk
    assert order.lines.filter(accounting_identifier="strawberries").first().extra_data["runner"] == "runner"


@pytest.mark.django_db
def test_order_creator_with_package_product(rf, admin_user):
    if "shuup.simple_supplier" not in settings.INSTALLED_APPS:
        pytest.skip("Need shuup.simple_supplier in INSTALLED_APPS")
    from shuup_tests.simple_supplier.utils import get_simple_supplier

    shop = get_default_shop()
    supplier = get_simple_supplier()
    package_product = create_package_product("Package-Product-Test", shop=shop, supplier=supplier, children=2)
    shop_product = package_product.get_shop_instance(shop)
    quantity_map = package_product.get_package_child_to_quantity_map()
    product_1, product_2 = quantity_map.keys()

    assert quantity_map[product_1] == 1
    assert quantity_map[product_2] == 2

    supplier.adjust_stock(product_1.pk, 1)
    supplier.adjust_stock(product_2.pk, 2)

    assert supplier.get_stock_status(product_1.pk).logical_count == 1
    assert supplier.get_stock_status(product_2.pk).logical_count == 2

    creator = OrderCreator()

    # There should be no exception when creating order with only package product
    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=package_product,
        supplier=supplier,
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    order = creator.create_order(source)

    # However, there should not be enough stock for both package and child products
    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=package_product,
        supplier=supplier,
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product_1,
        supplier=supplier,
        quantity=1,
        base_unit_price=source.create_price(10),
    )

    # And a validation error should be raised
    with pytest.raises(ValidationError):
        order = creator.create_order(source)


@pytest.mark.django_db
def test_order_creator_supplierless_product_line_conversion_should_fail(rf, admin_user):
    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=None,
        quantity=1,
        base_unit_price=source.create_price(10),
    )

    creator = OrderCreator()
    with pytest.raises(ValueError):
        order = creator.create_order(source)


@pytest.mark.django_db
def test_order_creator_orderability(admin_user):
    source = OrderSource(get_default_shop())
    product = get_default_product()

    line = source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=get_default_supplier(source.shop),
        quantity=1,
        shop=get_default_shop(),
        base_unit_price=source.create_price(10),
    )
    assert len(list(source.get_validation_errors())) == 0

    # delete the shop product
    product.get_shop_instance(get_default_shop()).delete()

    errors = list(source.get_validation_errors())
    assert len(errors) == 1
    assert "product_not_available_in_shop" in errors[0].code


@pytest.mark.django_db
def test_processor_orderability(admin_user):
    source = OrderSource(get_default_shop())
    processor = OrderProcessor()
    line = source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(source.shop),
        quantity=1,
        shop=get_default_shop(),
        base_unit_price=source.create_price(10),
    )
    line.order = Order(shop=source.shop)
    assert processor._check_orderability(line) is None

    unorderable_line = source.add_line(
        type=OrderLineType.PRODUCT,
        product=create_product("no-shop"),
        supplier=get_default_supplier(source.shop),
        quantity=1,
        shop=source.shop,
        base_unit_price=source.create_price(20),
    )
    unorderable_line.order = Order(shop=source.shop)
    with pytest.raises(ValidationError) as exc:
        processor._check_orderability(unorderable_line)
    assert "is not available in" in exc.value.message


@pytest.mark.django_db
def test_order_source_parentage(rf, admin_user):
    source = seed_source(admin_user)
    product = get_default_product()
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=get_default_supplier(source.shop),
        quantity=1,
        base_unit_price=source.create_price(10),
        line_id="parent",
    )
    source.add_line(
        type=OrderLineType.OTHER,
        text="Child Line",
        sku="KIDKIDKID",
        quantity=1,
        base_unit_price=source.create_price(5),
        parent_line_id="parent",
    )

    creator = OrderCreator()
    order = Order.objects.get(pk=creator.create_order(source).pk)
    kid_line = order.lines.filter(sku="KIDKIDKID").first()
    assert kid_line
    assert kid_line.parent_line.product_id == product.pk


@pytest.mark.django_db
def test_order_source_extra_data(rf, admin_user):
    source = seed_source(admin_user)
    product = get_default_product()
    line1 = source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=get_default_supplier(source.shop),
        quantity=1,
        base_unit_price=source.create_price(10),
        line_id="parent",
    )
    line2 = source.add_line(
        type=OrderLineType.OTHER,
        text="Child Line",
        sku="KIDKIDKID",
        quantity=1,
        base_unit_price=source.create_price(5),
        parent_line_id="parent",
    )

    creator = OrderCreator()
    order = Order.objects.get(pk=creator.create_order(source).pk)
    line_ids = [line.extra_data["source_line_id"] for line in order.lines.all()]
    assert line1.line_id in line_ids
    assert line2.line_id in line_ids


@pytest.mark.django_db
def test_order_creator_min_total(rf, admin_user):
    shop = get_default_shop()
    configuration.set(shop, ORDER_MIN_TOTAL_CONFIG_KEY, Decimal(20))

    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(shop),
        quantity=1,
        base_unit_price=source.create_price(10),
    )

    creator = OrderCreator()
    with pytest.raises(ValidationError):
        creator.create_order(source)

    configuration.set(shop, ORDER_MIN_TOTAL_CONFIG_KEY, Decimal(1))
    creator.create_order(source)

    # do not mess with other tests
    configuration.set(shop, ORDER_MIN_TOTAL_CONFIG_KEY, Decimal(0))


@pytest.mark.django_db
def test_order_creator_contact_multishop():
    with override_settings(SHUUP_MANAGE_CONTACTS_PER_SHOP=True, SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        user = create_random_user()
        customer = create_random_person("en")
        customer.user = user
        customer.save()
        shop = get_shop(identifier="random-shop", enabled=True)

        source = seed_source(user, shop)
        source.add_line(
            type=OrderLineType.PRODUCT,
            product=get_default_product(),
            supplier=get_default_supplier(shop),
            quantity=1,
            base_unit_price=source.create_price(10),
        )
        creator = OrderCreator()
        creator.create_order(source)
        customer.refresh_from_db()
        assert shop in customer.shops.all()


@pytest.mark.django_db
def test_order_creator_company_multishop():
    with override_settings(SHUUP_MANAGE_CONTACTS_PER_SHOP=True, SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        company = create_random_company()
        shop = get_shop(identifier="random-shop", enabled=True)

        source = seed_source(create_random_user(), shop)
        source.customer = company
        source.add_line(
            type=OrderLineType.PRODUCT,
            product=get_default_product(),
            supplier=get_default_supplier(shop),
            quantity=1,
            base_unit_price=source.create_price(10),
        )
        creator = OrderCreator()
        creator.create_order(source)
        company.refresh_from_db()
        assert shop in company.shops.all()


@pytest.mark.django_db
def test_order_customer_groups(rf, admin_user):
    customer = create_random_person()
    default_group = get_default_customer_group()
    default_group.members.add(customer)
    source = seed_source(admin_user)
    source.customer = customer

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(source.shop),
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    source.add_line(
        type=OrderLineType.OTHER,
        quantity=1,
        base_unit_price=source.create_price(10),
        require_verification=True,
    )

    creator = OrderCreator()
    order = creator.create_order(source)
    assert get_data_dict(source.billing_address) == get_data_dict(order.billing_address)
    assert get_data_dict(source.shipping_address) == get_data_dict(order.shipping_address)
    customer = source.customer
    assert customer == order.customer
    assert customer.groups.count() == 2
    assert order.customer_groups.filter(id=default_group.id).exists()
    with pytest.raises(ProtectedError):
        default_group.delete()

    assert customer.tax_group is not None
    assert customer.tax_group == order.tax_group
    with pytest.raises(ProtectedError):
        customer.tax_group.delete()

    new_group = create_random_contact_group()
    new_group.members.add(customer)

    order.phone = "911"
    order.save()
    assert order.customer_groups.filter(id=default_group.id).exists()
    assert not order.customer_groups.filter(id=new_group.id).exists()


@pytest.mark.django_db
def test_order_creator_account_manager():
    company = create_random_company()
    shop = get_shop(identifier="random-shop", enabled=True)
    source = seed_source(create_random_user(), shop)
    source.customer = company
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(shop),
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    creator = OrderCreator()
    order = creator.create_order(source)
    assert order.account_manager is None  # Company contact doesn't have account manager field

    person = create_random_person()
    person.account_manager = create_random_person()
    person.save()

    source = seed_source(create_random_user(), shop)
    source.customer = person
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(shop),
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    creator = OrderCreator()
    order = creator.create_order(source)
    assert order.account_manager is not None
    assert order.account_manager == person.account_manager
    with pytest.raises(ProtectedError):
        person.account_manager.delete()


@pytest.mark.django_db
def test_order_copy_by_updating_order_source_from_order(admin_user):
    shop = get_default_shop()

    line_data = {
        "type": OrderLineType.PRODUCT,
        "product": get_default_product(),
        "supplier": get_default_supplier(shop),
        "quantity": 1,
        "base_unit_price": shop.create_price(10),
    }
    source = seed_source(admin_user)
    source.add_line(**line_data)
    source.payment_data = None

    creator = OrderCreator()
    order = creator.create_order(source)

    new_source = OrderSource(shop)
    new_source.update_from_order(order)
    new_source.add_line(**line_data)

    new_order = creator.create_order(new_source)
    assert new_order
    assert order.billing_address == new_order.billing_address
    assert order.taxful_total_price == new_order.taxful_total_price


@pytest.mark.parametrize("include_tax", [True, False])
@pytest.mark.django_db
def test_order_creator_taxes(admin_user, include_tax):
    shop = get_shop(include_tax)
    source = OrderSource(shop)
    source.status = get_initial_order_status()
    create_default_order_statuses()
    tax = get_tax("sales-tax", "Sales Tax", Decimal(0.2))  # 20%
    create_default_tax_rule(tax)
    product = get_default_product()

    line = source.add_line(
        line_id="product-line",
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=get_default_supplier(shop),
        quantity=1,
        shop=shop,
        base_unit_price=source.create_price(100),
    )
    discount_line = source.add_line(
        line_id="discount-line",
        type=OrderLineType.DISCOUNT,
        supplier=get_default_supplier(shop),
        quantity=1,
        base_unit_price=source.create_price(0),
        discount_amount=source.create_price(100),
        parent_line_id=line.line_id,
    )
    assert source.taxful_total_price.value == Decimal()
    creator = OrderCreator()
    order = creator.create_order(source)
    assert order.taxful_total_price.value == Decimal()
