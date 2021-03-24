# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from shuup.core.models import (
    ProductMode,
    ProductVariationResult,
    ProductVariationVariable,
    ProductVariationVariableValue,
    ShopProduct,
    ShopProductVisibility,
)
from shuup.testing.factories import create_product, get_default_shop


@pytest.mark.django_db
def test_simple_variation():
    shop = get_default_shop()
    parent = create_product("SimpleVarParent")
    children = [create_product("SimpleVarChild-%d" % x) for x in range(10)]
    for child in children:
        child.link_to_parent(parent)
        sp = ShopProduct.objects.create(shop=shop, product=child, visibility=ShopProductVisibility.ALWAYS_VISIBLE)
        assert child.is_variation_child()
        assert not sp.is_list_visible()  # Variation children are not list visible

    assert parent.mode == ProductMode.SIMPLE_VARIATION_PARENT
    assert not list(parent.get_all_available_combinations())  # Simple variations can't have these.

    # Validation tests

    dummy = create_product("InvalidSimpleVarChild")

    with pytest.raises(ValueError):
        dummy.link_to_parent(parent, variables={"size": "XL"})

    with pytest.raises(ValueError):
        parent.link_to_parent(dummy)

    with pytest.raises(ValueError):
        dummy.link_to_parent(children[0])

    # Unlinkage

    for child in children:
        child.unlink_from_parent()
        assert not child.is_variation_child()
        assert child.mode == ProductMode.NORMAL

    assert not parent.is_variation_parent()
    assert parent.variation_children.count() == 0


@pytest.mark.django_db
def test_variable_variation():
    parent = create_product("ComplexVarParent")
    sizes_and_children = [("%sL" % ("X" * x), create_product("ComplexVarChild-%d" % x)) for x in range(4)]
    for size, child in sizes_and_children:
        child.link_to_parent(parent, variables={"size": size})
    assert parent.mode == ProductMode.VARIABLE_VARIATION_PARENT
    assert all(child.is_variation_child() for (size, child) in sizes_and_children)

    # Validation tests

    dummy = create_product("InvalidComplexVarChild")

    with pytest.raises(ValueError):
        dummy.link_to_parent(parent)

    with pytest.raises(ValueError):
        parent.link_to_parent(dummy)

    with pytest.raises(ValueError):
        dummy.link_to_parent(sizes_and_children[0][1])

    # Variable tests

    size_attr = parent.variation_variables.get(identifier="size")

    for size, child in sizes_and_children:
        size_val = size_attr.values.get(identifier=size)
        result_product = ProductVariationResult.resolve(parent, {size_attr: size_val})
        assert result_product == child


@pytest.mark.django_db
def test_multivariable_variation():
    parent = create_product("SuperComplexVarParent")
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
        # Elide a combination (yellow/small) for testing:
        if (
            combo["variable_to_value"][color_var].identifier == "yellow"
            and combo["variable_to_value"][size_var].identifier == "small"
        ):
            continue
        child = create_product("xyz-%s" % combo["sku_part"])
        child.link_to_parent(parent, combo["variable_to_value"])
    assert parent.mode == ProductMode.VARIABLE_VARIATION_PARENT

    # Elided product should not yield a result
    yellow_color_value = ProductVariationVariableValue.objects.get(variable=color_var, identifier="yellow")
    small_size_value = ProductVariationVariableValue.objects.get(variable=size_var, identifier="small")
    assert not ProductVariationResult.resolve(parent, {color_var: yellow_color_value, size_var: small_size_value})
    # Anything else should
    brown_color_value = ProductVariationVariableValue.objects.get(variable=color_var, identifier="brown")
    result1 = ProductVariationResult.resolve(parent, {color_var: brown_color_value, size_var: small_size_value})
    result2 = ProductVariationResult.resolve(
        parent, {color_var.pk: brown_color_value.pk, size_var.pk: small_size_value.pk}
    )
    assert result1 and result2
    assert result1.pk == result2.pk

    assert len(parent.get_available_variation_results()) == (3 * 4 - 1)


@pytest.mark.django_db
def test_parent_mode_changes_to_normal_when_no_valid_children():
    shop = get_default_shop()
    parent = create_product("SimpleVarParent")
    children = [create_product("SimpleVarChild-%d" % x) for x in range(10)]
    for child in children:
        child.link_to_parent(parent)
        ShopProduct.objects.create(shop=shop, product=child, visibility=ShopProductVisibility.ALWAYS_VISIBLE)
    parent.verify_mode()
    assert parent.variation_children.count() == 10
    assert parent.mode == ProductMode.SIMPLE_VARIATION_PARENT

    # Delete all variation children
    [product.soft_delete() for product in parent.variation_children.all()]

    # Parent has no non-deleted variation children so it's turned back into a normal product
    parent.verify_mode()
    assert parent.variation_children.filter(deleted=False).count() == 0
    assert parent.mode == ProductMode.NORMAL
