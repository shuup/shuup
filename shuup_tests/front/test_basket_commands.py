# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http.response import HttpResponseRedirect, JsonResponse

from shuup.core.models import (
    ProductVariationVariable, ProductVariationVariableValue, ShopProductVisibility
)
from shuup.front.basket import commands as basket_commands
from shuup.front.basket import get_basket_command_dispatcher
from shuup.front.basket.command_dispatcher import BasketCommandDispatcher
from shuup.front.signals import get_basket_command_handler
from shuup.testing.factories import (
    create_product, get_default_product, get_default_shop,
    get_default_supplier
)
from shuup_tests.front.fixtures import get_request_with_basket


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
    product = get_default_product()
    supplier = get_default_supplier()
    request = get_request_with_basket()
    basket = request.basket

    with pytest.raises(ValidationError):
        basket_commands.handle_add(request, basket, product_id=product.pk, quantity=-3)  # Ordering antimatter is not supported

    # These will get merged into one line...
    basket_commands.handle_add(request, basket, **{"product_id": product.pk, "quantity": 1, "supplier_id": supplier.pk})
    basket_commands.handle_add(request, basket, **{"product_id": product.pk, "quantity": 2})
    # ... so there will be 3 products but one line
    assert basket.product_count == 3
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
    product = get_default_product()
    basket_commands.handle_add(request, basket, product_id=product.pk, quantity=1)
    assert basket.product_count == 1
    line_id = basket.get_lines()[0].line_id
    basket_commands.handle_update(request, basket, **{"q_%s" % line_id: "2"})
    assert basket.product_count == 2
    basket_commands.handle_update(request, basket, **{"delete_%s" % line_id: "1"})
    assert basket.product_count == 0


@pytest.mark.django_db
def test_basket_update_errors():
    request = get_request_with_basket()
    basket = request.basket
    product = get_default_product()
    basket_commands.handle_add(request, basket, product_id=product.pk, quantity=1)
    line_id = basket.get_lines()[0].line_id

    # Hide product and now updating quantity should give errors
    shop_product = product.get_shop_instance(request.shop)
    shop_product.suppliers.clear()

    basket_commands.handle_update(request, basket, **{"q_%s" % line_id: "2"})
    error_messages = messages.get_messages(request)
    # One warning is added to messages
    assert len(error_messages) == 1
    assert any("not supplied" in msg.message for msg in error_messages)

    shop_product.visibility = ShopProductVisibility.NOT_VISIBLE
    shop_product.save()

    basket_commands.handle_update(request, basket, **{"q_%s" % line_id: "2"})

    error_messages = messages.get_messages(request)
    # Two warnings is added to messages
    assert len(error_messages) == 3
    assert any("not visible" in msg.message for msg in error_messages)
    assert all("[" not in msg.message for msg in error_messages)


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
