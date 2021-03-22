# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http.response import HttpResponseRedirect, JsonResponse

from shuup.campaigns.models.basket_conditions import BasketTotalAmountCondition
from shuup.campaigns.models.basket_effects import BasketDiscountAmount
from shuup.campaigns.models.campaigns import BasketCampaign
from shuup.core.basket.update_methods import BasketUpdateMethods
from shuup.core.excs import ProductNotOrderableProblem
from shuup.core.models import (
    OrderLineType,
    ProductMode,
    ProductVariationVariable,
    ProductVariationVariableValue,
    SalesUnit,
    ShopProductVisibility,
)
from shuup.core.order_creator import OrderLineBehavior
from shuup.front.basket import commands as basket_commands, get_basket, get_basket_command_dispatcher
from shuup.front.basket.command_dispatcher import BasketCommandDispatcher
from shuup.front.signals import get_basket_command_handler
from shuup.testing.factories import (
    complete_product,
    create_product,
    create_random_person,
    get_default_product,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.front.fixtures import get_request_with_basket

from .utils import get_unstocked_package_product_and_stocked_child


class ReturnUrlBasketCommandDispatcher(BasketCommandDispatcher):
    def postprocess_response(self, command, kwargs, response):
        response["return"] = "/dummy/"
        return response


@pytest.mark.django_db
def test_dne():
    commands = get_basket_command_dispatcher(get_request_with_basket())
    with pytest.raises(Exception):
        commands.handle("_doesnotexist_")


@pytest.mark.django_db
def test_add_and_remove_and_clear():
    product = create_product("fractionable", fractional=True)
    complete_product(product)
    supplier = get_default_supplier()
    request = get_request_with_basket()
    basket = request.basket

    with pytest.raises(ValidationError):
        # Ordering antimatter is not supported
        basket_commands.handle_add(request, basket, product_id=product.pk, quantity=-3)

    # These will get merged into one line...
    basket_commands.handle_add(request, basket, **{"product_id": product.pk, "quantity": 1, "supplier_id": supplier.pk})
    basket_commands.handle_add(request, basket, **{"product_id": product.pk, "quantity": 2})

    # Fractions should also be supported
    basket_commands.handle_add(request, basket, **{"product_id": product.pk, "quantity": 0.75})

    # ... so there will be 3 products but one line
    assert basket.product_count == 3.75
    lines = basket.get_lines()
    assert len(lines) == 1
    # ... and deleting that line will clear the basket...
    basket_commands.handle_del(request, basket, lines[0].line_id)
    assert basket.product_count == 0
    # ... and adding another product will create a new line...
    basket_commands.handle_add(request, basket, product_id=product.pk, quantity=1)
    assert basket.product_count == 1
    # ... that can be cleared.
    basket_commands.handle_clear(request, basket)
    assert basket.product_count == 0


@pytest.mark.django_db
def test_add_and_invalid_product():
    shop = get_default_shop()
    product = create_product("fractionable", fractional=True)
    complete_product(product)
    supplier = get_default_supplier()
    request = get_request_with_basket()
    basket = request.basket

    # remove the shop product
    product.get_shop_instance(shop).delete()

    with pytest.raises(ValidationError) as exc:
        basket_commands.handle_add(
            request, basket, **{"product_id": product.pk, "quantity": 1, "supplier_id": supplier.pk}
        )
    assert "Product is not available in this shop" in exc.value.message


@pytest.mark.django_db
def test_add_invalid_product():
    shop = get_default_shop()
    supplier = get_default_supplier()
    request = get_request_with_basket()
    basket = request.basket

    # cannot add simple/variable variation parent to the basket
    parent = create_product("parent", shop=shop, supplier=supplier)
    child = create_product("child", shop=shop, supplier=supplier)
    child.link_to_parent(parent)
    parent.refresh_from_db()
    assert parent.mode == ProductMode.SIMPLE_VARIATION_PARENT

    with pytest.raises(ValidationError) as excinfo:
        basket_commands.handle_add(request, basket, product_id=parent.pk, quantity=2)
    assert excinfo.value.code == "invalid_product"

    child.unlink_from_parent()
    child.link_to_parent(parent, variables={"size": "XXL"})
    parent.refresh_from_db()
    assert parent.mode == ProductMode.VARIABLE_VARIATION_PARENT

    with pytest.raises(ValidationError) as excinfo:
        basket_commands.handle_add(request, basket, product_id=parent.pk, quantity=3)
    assert excinfo.value.code == "invalid_product"


@pytest.mark.django_db
def test_ajax():
    product = get_default_product()
    commands = get_basket_command_dispatcher(get_request_with_basket())
    commands.ajax = True
    rv = commands.handle("add", kwargs=dict(product_id=product.pk, quantity=-3))
    assert isinstance(rv, JsonResponse)
    assert commands.basket.product_count == 0


@pytest.mark.django_db
def test_nonajax():
    product = get_default_product()
    commands = get_basket_command_dispatcher(get_request_with_basket())
    commands.ajax = False
    with pytest.raises(Exception):
        commands.handle("add", kwargs=dict(product_id=product.pk, quantity=-3))


@pytest.mark.django_db
def test_redirect():
    commands = ReturnUrlBasketCommandDispatcher(request=get_request_with_basket())
    commands.ajax = False
    assert isinstance(commands.handle("clear"), HttpResponseRedirect)


@pytest.mark.django_db
def test_variation():
    request = get_request_with_basket()
    basket = request.basket
    shop = get_default_shop()
    supplier = get_default_supplier()

    parent = create_product("BuVarParent", shop=shop, supplier=supplier)
    child = create_product("BuVarChild", shop=shop, supplier=supplier)
    child.link_to_parent(parent, variables={"test": "very"})
    attr = parent.variation_variables.get(identifier="test")
    val = attr.values.get(identifier="very")
    basket_commands.handle_add_var(request, basket, parent.id, **{"var_%s" % attr.id: val.id})
    assert basket.get_product_ids_and_quantities()[child.pk] == 1

    with pytest.raises(ValidationError):
        basket_commands.handle_add_var(request, basket, parent.id, **{"var_%s" % attr.id: (val.id + 1)})


@pytest.mark.django_db
def test_complex_variation():
    request = get_request_with_basket()
    basket = request.basket
    shop = get_default_shop()
    supplier = get_default_supplier()

    parent = create_product("SuperComplexVarParent", shop=shop, supplier=supplier)
    color_var = ProductVariationVariable.objects.create(product=parent, identifier="color")
    size_var = ProductVariationVariable.objects.create(product=parent, identifier="size")

    ProductVariationVariableValue.objects.create(variable=color_var, identifier="yellow")
    ProductVariationVariableValue.objects.create(variable=size_var, identifier="small")

    combinations = list(parent.get_all_available_combinations())
    for combo in combinations:
        child = create_product("xyz-%s" % combo["sku_part"], shop=shop, supplier=supplier)
        child.link_to_parent(parent, combo["variable_to_value"])

    # Elided product should not yield a result
    yellow_color_value = ProductVariationVariableValue.objects.get(variable=color_var, identifier="yellow")
    small_size_value = ProductVariationVariableValue.objects.get(variable=size_var, identifier="small")
    # add to basket yellow + small
    kwargs = {"var_%d" % color_var.pk: yellow_color_value.pk, "var_%d" % size_var.pk: small_size_value.pk}
    basket_commands.handle_add_var(request, basket, parent.id, **kwargs)
    assert basket.get_product_ids_and_quantities()[child.pk] == 1

    with pytest.raises(ValidationError):
        kwargs = {"var_%d" % color_var.pk: yellow_color_value.pk, "var_%d" % size_var.pk: small_size_value.pk + 1}
        basket_commands.handle_add_var(request, basket, parent.id, **kwargs)


@pytest.mark.django_db
def test_basket_update():
    request = get_request_with_basket()
    basket = request.basket
    product = create_product("fractionable", fractional=True)
    complete_product(product)
    basket_commands.handle_add(request, basket, product_id=product.pk, quantity=1.75)
    assert basket.product_count == 1.75
    line_id = basket.get_lines()[0].line_id
    basket_commands.handle_update(request, basket, **{"q_%s" % line_id: "2"})
    assert basket.product_count == 2
    basket_commands.handle_update(request, basket, **{"delete_%s" % line_id: "1"})
    assert basket.product_count == 0


@pytest.mark.django_db
def test_basket_partial_quantity_update():
    request = get_request_with_basket()
    basket = request.basket
    product = get_default_product()

    sales_unit = SalesUnit.objects.create(identifier="test-sales-partial", decimals=2, name="Partial unit")
    product.sales_unit = sales_unit  # Set the sales unit for the product
    product.save()

    basket_commands.handle_add(request, basket, product_id=product.pk, quantity=1.5)
    assert basket.product_count == 1.5
    line_id = basket.get_lines()[0].line_id
    basket_commands.handle_update(request, basket, **{"q_%s" % line_id: "1.5"})
    assert basket.product_count == 1.5

    basket_commands.handle_update(request, basket, **{"q_%s" % line_id: "3.5"})
    assert basket.product_count == 3.5

    basket_commands.handle_update(request, basket, **{"q_%s" % line_id: "3.0"})
    assert basket.product_count == 3.0

    basket_commands.handle_update(request, basket, **{"q_%s" % line_id: "4"})
    assert basket.product_count == 4

    basket_commands.handle_update(request, basket, **{"delete_%s" % line_id: "1"})
    assert basket.product_count == 0


@pytest.mark.django_db
def test_basket_partial_quantity_update_all_product_counts():
    shop = get_default_shop()
    supplier = get_default_supplier()
    request = get_request_with_basket()
    basket = request.basket

    pieces = SalesUnit.objects.create(identifier="pieces", decimals=0, name="Pieces", symbol="pc.")
    kilograms = SalesUnit.objects.create(identifier="kilograms", decimals=3, name="Kilograms", symbol="kg")
    cup = create_product(sku="COFFEE-CUP-123", sales_unit=pieces, shop=shop, supplier=supplier)
    beans = create_product(sku="COFFEEBEANS3", sales_unit=kilograms, shop=shop, supplier=supplier)
    beans_shop_product = beans.get_shop_instance(shop)
    beans_shop_product.minimum_purchase_quantity = Decimal("0.1")
    beans_shop_product.save()
    pears = create_product(sku="PEARS-27", sales_unit=kilograms, shop=shop, supplier=supplier)

    add = basket_commands.handle_add
    update = basket_commands.handle_update

    # Empty basket
    assert basket.product_count == 0
    assert basket.smart_product_count == 0
    assert basket.product_line_count == 0

    # 1 cup
    add(request, basket, product_id=cup.pk, quantity=1)
    assert basket.product_count == 1
    assert basket.smart_product_count == 1
    assert basket.product_line_count == 1

    # Basket update operations work by prefixing line id with operation
    qty_update_cup = "q_" + basket.get_lines()[0].line_id
    delete_cup = "delete_" + basket.get_lines()[0].line_id

    # 3 cups
    update(request, basket, **{qty_update_cup: "3"})
    assert basket.product_count == 3
    assert basket.smart_product_count == 3
    assert basket.product_line_count == 1

    # 3 cups + 0.5 kg beans
    add(request, basket, product_id=beans.pk, quantity="0.5")
    assert basket.product_count == Decimal("3.5")
    assert basket.smart_product_count == 4
    assert basket.product_line_count == 2

    qty_update_beans = "q_" + basket.get_lines()[1].line_id
    delete_beans1 = "delete_" + basket.get_lines()[1].line_id

    # 1 cup + 2.520 kg beans
    update(request, basket, **{qty_update_cup: "1.0"})
    update(request, basket, **{qty_update_beans: "2.520"})
    assert basket.product_count == Decimal("3.520")
    assert basket.smart_product_count == 2
    assert basket.product_line_count == 2

    # 42 cups + 2.520 kg beans
    update(request, basket, **{qty_update_cup: "42"})
    assert basket.product_count == Decimal("44.520")
    assert basket.smart_product_count == 43
    assert basket.product_line_count == 2

    # 42 cups + 2.520 kg beans + 3.5 kg pears
    add(request, basket, product_id=pears.pk, quantity="3.5")
    assert basket.product_count == Decimal("48.020")
    assert basket.smart_product_count == 44
    assert basket.product_line_count == 3

    # 42 cups + 3.5 kg pears
    update(request, basket, **{delete_beans1: "1"})
    assert basket.product_count == Decimal("45.5")
    assert basket.smart_product_count == 43
    assert basket.product_line_count == 2

    # 3.5 kg pears
    update(request, basket, **{delete_cup: "1"})
    assert basket.product_count == Decimal("3.5")
    assert basket.smart_product_count == 1
    assert basket.product_line_count == 1


@pytest.mark.django_db
def test_basket_update_with_package_product():
    if "shuup.simple_supplier" not in settings.INSTALLED_APPS:
        pytest.skip("Need shuup.simple_supplier in INSTALLED_APPS")
    from shuup_tests.simple_supplier.utils import get_simple_supplier

    request = get_request_with_basket()
    basket = request.basket
    shop = get_default_shop()
    supplier = get_simple_supplier()
    parent, child = get_unstocked_package_product_and_stocked_child(shop, supplier, child_logical_quantity=2)

    # There should be enough stock for 1 parent and 1 extra child, each of quantity 1
    basket_commands.handle_add(request, basket, product_id=parent.pk, quantity=1)
    assert basket.product_count == 1
    basket_commands.handle_add(request, basket, product_id=child.pk, quantity=1)
    assert basket.product_count == 2
    assert not messages.get_messages(request)

    basket_lines = {line.product.id: line for line in basket.get_lines()}
    package_line = basket_lines[parent.id]
    extra_child_line = basket_lines[child.id]

    # Trying to increase package product line quantity should fail, with error message
    basket_commands.handle_update(request, basket, **{"q_%s" % package_line.line_id: "2"})
    assert basket.product_count == 2
    assert len(messages.get_messages(request)) == 1

    # So should increasing the extra child line quantity
    basket_commands.handle_update(request, basket, **{"q_%s" % extra_child_line.line_id: "2"})
    assert basket.product_count == 2
    assert len(messages.get_messages(request)) == 2

    # However, if we delete the parent line, we can increase the extra child
    basket_commands.handle_update(request, basket, **{"delete_%s" % package_line.line_id: "1"})
    assert basket.product_count == 1
    basket_commands.handle_update(request, basket, **{"q_%s" % extra_child_line.line_id: "2"})
    assert basket.product_count == 2

    # Resetting to original basket contents
    basket_commands.handle_update(request, basket, **{"q_%s" % extra_child_line.line_id: "1"})
    basket_commands.handle_add(request, basket, product_id=parent.pk, quantity=1)
    basket_lines = {line.product.id: line for line in basket.get_lines()}
    package_line = basket_lines[parent.id]  # Package line will have a new ID
    assert basket.product_count == 2

    # Like above, delete the child line and we can now increase the parent
    basket_commands.handle_update(request, basket, **{"delete_%s" % extra_child_line.line_id: "1"})
    assert basket.product_count == 1
    basket_commands.handle_update(request, basket, **{"q_%s" % package_line.line_id: "2"})
    assert basket.product_count == 2

    # Clear basket
    basket_commands.handle_clear(request, basket)
    assert basket.product_count == 0

    # Remove the Shop Product from the child
    child.get_shop_instance(shop).delete()

    # Child not available for this shop
    with pytest.raises(ProductNotOrderableProblem):
        basket_commands.handle_add(request, basket, product_id=parent.pk, quantity=1)

    # use the update methods object to check orderability errors
    update_methods = BasketUpdateMethods(request, basket)
    errors = update_methods._get_orderability_errors(parent, supplier, 1)
    assert len(errors) == 2
    assert any(["product_not_available_in_shop" in error.code for error in errors])


@pytest.mark.django_db
def test_custom_basket_command():
    ok = []

    def noop(**kwargs):
        ok.append(kwargs)

    def get_custom_command(command, **kwargs):
        if command == "test_custom_basket_command":
            return noop

    old_n_receivers = len(get_basket_command_handler.receivers)
    try:
        get_basket_command_handler.connect(get_custom_command, dispatch_uid="test_custom_basket_command")
        commands = get_basket_command_dispatcher(request=get_request_with_basket())
        commands.handle("test_custom_basket_command")
        assert ok  # heh.
    finally:
        get_basket_command_handler.disconnect(dispatch_uid="test_custom_basket_command")
        assert old_n_receivers == len(get_basket_command_handler.receivers)


@pytest.mark.django_db
def test_parallel_baskets(rf):
    request = get_request_with_basket()
    shop = get_default_shop()
    customer = create_random_person()

    request = rf.get("/")
    request.shop = shop
    apply_request_middleware(request)
    request.customer = customer

    basket_one = get_basket(request, basket_name="basket_one")
    basket_two = get_basket(request, basket_name="basket_two")

    product_one = get_default_product()
    product_two = get_default_product()
    product_two.sku = "derpy-hooves"
    sales_unit = SalesUnit.objects.create(identifier="test-sales-partial", decimals=2, name="Partial unit")
    product_two.sales_unit = sales_unit  # Set the sales unit for the product
    product_two.save()

    basket_commands.handle_add(request, basket_one, product_id=product_one.pk, quantity=1)
    basket_commands.handle_add(request, basket_two, product_id=product_two.pk, quantity=3.5)

    assert basket_one.product_count == 1
    assert basket_two.product_count == 3.5


@pytest.mark.django_db
def test_basket_update_with_discount():
    supplier = get_default_supplier()
    request = get_request_with_basket()
    basket = request.basket
    default_price = 10
    product = create_product(
        "fractionable", fractional=True, default_price=default_price, shop=basket.shop, supplier=supplier
    )
    discount_amount_value = 4
    basket_rule1 = BasketTotalAmountCondition.objects.create(value="2")
    campaign = BasketCampaign.objects.create(shop=basket.shop, public_name="test", name="test", active=True)
    campaign.conditions.add(basket_rule1)
    campaign.save()
    BasketDiscountAmount.objects.create(campaign=campaign, discount_amount=discount_amount_value)
    # basket_commands.handle_add(request, basket, product_id=product.pk, quantity=1)
    basket.add_line(
        line_id="product-line",
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=supplier,
        quantity=1,
        shop=basket.shop,
    )
    line_id = basket.get_lines()[0].line_id
    basket_commands.handle_update(request, basket, **{"q_%s" % line_id: "2"})
    basket.uncache()
    assert basket.product_count == 2
    assert OrderLineType.DISCOUNT in [l.type for l in basket.get_final_lines()]
    basket.clear_all()
    basket.add_line(
        line_id="product-line",
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=supplier,
        quantity=1,
        shop=basket.shop,
        on_parent_change_behavior=OrderLineBehavior.SKIP,
    )
    line_id = basket.get_lines()[0].line_id

    basket_commands.handle_update(request, basket, **{"q_%s" % line_id: "3"})
    assert basket.product_count == 1

    basket.clear_all()
    basket.add_line(
        line_id="product-line",
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=supplier,
        quantity=1,
        shop=basket.shop,
        on_parent_change_behavior=OrderLineBehavior.DELETE,
    )
    line_id = basket.get_lines()[0].line_id

    basket_commands.handle_update(request, basket, **{"q_%s" % line_id: "4"})
    assert basket.product_count == 0
