# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal

import six
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import Product, ProductVariationResult
from shuup.core.order_creator import is_code_usable
from shuup.utils.importing import cached_load
from shuup.utils.numbers import parse_decimal_string


# TODO: Refactor handle_add, it's too complex
def handle_add(request, basket, product_id, quantity=1, supplier_id=None, **kwargs):  # noqa (C901)
    """
    Handle adding a product to the basket.

    :param product_id: product ID to add (or if `child_product_id` is truey, the parent ID)
    :param quantity: quantity of products to add
    :param child_product_id: child product ID to add (if truey)
    :param supplier_id: The supplier ID for the new line. If None, the first supplier is used.
    """
    product_id = int(product_id)

    product = get_object_or_404(Product, pk=product_id)
    shop_product = product.get_shop_instance(shop=request.shop)
    if not shop_product:
        raise ValidationError("Product not available in this shop", code="product_not_available_in_shop")

    if supplier_id:
        supplier = shop_product.suppliers.filter(pk=supplier_id).first()
    else:
        supplier = shop_product.suppliers.first()

    if not supplier:
        raise ValidationError("Invalid supplier", code="invalid_supplier")

    try:
        quantity = parse_decimal_string(quantity)
        if not product.sales_unit.allow_fractions:
            if quantity % 1 != 0:
                msg = _(
                    "The quantity %f is not allowed. "
                    "Please use an integer value.") % quantity
                raise ValidationError(msg, code="invalid_quantity")
            quantity = int(quantity)
    except (ValueError, decimal.InvalidOperation):
        raise ValidationError(_(u"The quantity %s is not valid.") % quantity, code="invalid_quantity")

    if quantity <= 0:
        raise ValidationError(_(u"The quantity %s is not valid.") % quantity, code="invalid_quantity")

    product_ids_and_quantities = basket.get_product_ids_and_quantities()
    already_in_basket_qty = product_ids_and_quantities.get(product.id, 0)
    shop_product.raise_if_not_orderable(
        supplier=supplier,
        quantity=(already_in_basket_qty + quantity),
        customer=basket.customer
    )

    # If the product is a package parent, also check child products
    if product.is_package_parent():
        for child_product, child_quantity in six.iteritems(product.get_package_child_to_quantity_map()):
            already_in_basket_qty = product_ids_and_quantities.get(child_product.id, 0)
            total_child_quantity = (quantity * child_quantity)
            sp = child_product.get_shop_instance(shop=request.shop)
            sp.raise_if_not_orderable(
                supplier=supplier,
                quantity=(already_in_basket_qty + total_child_quantity),
                customer=basket.customer
            )

    # TODO: Hook/extension point
    # if product.form:
    #     return {
    #         "error": u"Form required",
    #         "return": reverse_GET("product-form", kwargs={"pk": product.pk}, GET={"n": quantity})
    #     }

    add_product_kwargs = {
        "product": product,
        "quantity": quantity,
        "supplier": supplier,
        "shop": request.shop,
    }

    basket.add_product(**add_product_kwargs)

    return {
        'ok': basket.product_count,
        'added': quantity
    }


def handle_add_var(request, basket, product_id, quantity=1, **kwargs):
    """
    Handle adding a complex variable product into the basket by resolving the combination variables.
    This actually uses `kwargs`, expecting `var_XXX=YYY` to exist there, where `XXX` is the PK
    of a ProductVariationVariable and YYY is the PK of a ProductVariationVariableValue. Confused yet?

    :param quantity: Quantity of the resolved variation to add.
    :param kwargs: Expected to contain `var_*` values, see above.
    """

    # Resolve the combination...
    vars = dict((int(k.split("_")[-1]), int(v)) for (k, v) in six.iteritems(kwargs) if k.startswith("var_"))
    var_product = ProductVariationResult.resolve(product_id, combination=vars)
    if not var_product:
        raise ValidationError(_(u"This variation is not available."), code="invalid_variation_combination")
    # and hand it off to handle_add like we're used to
    return handle_add(request=request, basket=basket, product_id=var_product.pk, quantity=quantity)


def handle_del(request, basket, line_id, **kwargs):
    """
    Handle deleting a distinct order line from the basket given its unique line ID.

    :param line_id: The line ID to delete.
    :return:
    """
    return {'ok': basket.delete_line(int(line_id))}


def handle_clear(request, basket, **kwargs):
    """
    Handle fully clearing the basket.
    """

    basket.clear_all()
    return {'ok': True}


def handle_add_campaign_code(request, basket, code):
    if not code:
        return {"ok": False}

    if is_code_usable(basket, code):
        return {"ok": basket.add_code(code)}
    return {"ok": False}


def handle_update(request, basket, **kwargs):
    """
    Handle updating a basket, i.e. deleting some lines or updating quantities.

    This dispatches further to whatever is declared by the `SHUUP_BASKET_UPDATE_METHODS_SPEC`
    configuration entry.
    """
    methods = cached_load("SHUUP_BASKET_UPDATE_METHODS_SPEC")(request=request, basket=basket)
    prefix_method_dict = methods.get_prefix_to_method_map()
    basket_changed = False
    # If any POST items match a prefix defined in prefix_method_dict, call the appropriate model method.
    for key, value in six.iteritems(kwargs):
        for prefix, method in six.iteritems(prefix_method_dict):
            if key.startswith(prefix):
                line_id = key[len(prefix):]
                line = basket.find_line_by_line_id(line_id)
                field_changed = method(
                    key=key,
                    value=value,
                    line=line
                )
                basket_changed = (basket_changed or field_changed)
                break

    if basket_changed:  # pragma: no branch
        basket.clean_empty_lines()
        basket.dirty = True
