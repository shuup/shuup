# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import (
    Attribute,
    AttributeType,
    AttributeVisibility,
    ProductAttribute,
    ProductCrossSell,
    ProductCrossSellType,
    ShopProductVisibility,
)
from shuup.front.template_helpers import product as product_helpers
from shuup.testing.factories import create_product, get_default_shop, get_default_supplier
from shuup_tests.front.fixtures import get_jinja_context


def _create_cross_sell_products(product, shop, supplier, type, product_count, hidden=False):
    original_count = ProductCrossSell.objects.filter(product1=product, type=type).count()
    for count in range(product_count):
        related_product = create_product(
            "{}-test-sku-{}-{}".format(type, count, original_count),
            shop=shop,
            supplier=supplier,
        )
        ProductCrossSell.objects.create(product1=product, product2=related_product, type=type)
        if hidden:
            shop_product = related_product.get_shop_instance(shop)
            shop_product.visibility = ShopProductVisibility.NOT_VISIBLE
            shop_product.save()


@pytest.mark.django_db
def test_cross_sell_plugin_type(reindex_catalog):
    """
    Test that template helper returns correct number of cross sells when shop contains multiple
    relation types
    """
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("test-sku", shop=shop, supplier=supplier)
    context = get_jinja_context(product=product)
    type_counts = (
        (ProductCrossSellType.RELATED, 1),
        (ProductCrossSellType.RECOMMENDED, 2),
        (ProductCrossSellType.BOUGHT_WITH, 3),
    )

    # Create cross sell products and relations in different quantities
    for type, count in type_counts:
        _create_cross_sell_products(product, shop, supplier, type, count)
        assert ProductCrossSell.objects.filter(product1=product, type=type).count() == count

    reindex_catalog()

    # Make sure quantities returned by plugin match
    for type, count in type_counts:
        assert len(list(product_helpers.get_product_cross_sells(context, product, type, count))) == count


@pytest.mark.django_db
def test_bought_with_template_helper(reindex_catalog):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("test-sku", shop=shop, supplier=supplier)
    context = get_jinja_context(product=product)

    type = ProductCrossSellType.COMPUTED
    visible_count = 10
    hidden_count = 4
    _create_cross_sell_products(product, shop, supplier, type, visible_count)
    _create_cross_sell_products(product, shop, supplier, type, hidden_count, hidden=True)
    reindex_catalog()
    assert ProductCrossSell.objects.filter(product1=product, type=type).count() == (visible_count + hidden_count)

    # Make sure quantities returned by plugin match
    assert len(list(product_helpers.get_products_bought_with(context, product, visible_count))) == visible_count


@pytest.mark.django_db
def test_cross_sell_plugin_count(reindex_catalog):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("test-sku", shop=shop, supplier=supplier)
    context = get_jinja_context(product=product)
    total_count = 5
    trim_count = 3

    type = ProductCrossSellType.RELATED
    _create_cross_sell_products(product, shop, supplier, type, total_count)
    reindex_catalog()
    assert ProductCrossSell.objects.filter(product1=product, type=type).count() == total_count
    assert len(list(product_helpers.get_product_cross_sells(context, product, type, trim_count))) == trim_count


@pytest.mark.django_db
def test_visible_attributes():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("test-sku", shop=shop, supplier=supplier)

    _add_attribute_for_product(
        product, "attr1", AttributeType.BOOLEAN, AttributeVisibility.SHOW_ON_PRODUCT_PAGE, "attr1"
    )
    _add_attribute_for_product(product, "attr2", AttributeType.BOOLEAN, AttributeVisibility.HIDDEN, "attr2")

    assert len(product_helpers.get_visible_attributes(product)) == 1

    _add_attribute_for_product(
        product, "attr3", AttributeType.BOOLEAN, AttributeVisibility.SHOW_ON_PRODUCT_PAGE, "attr3"
    )

    assert len(product_helpers.get_visible_attributes(product)) == 2

    new_product = create_product("test-sku-2", shop=shop, supplier=supplier)
    ProductAttribute.objects.create(product=new_product, attribute=Attribute.objects.filter(identifier="attr1").first())

    assert len(product_helpers.get_visible_attributes(product)) == 2
    assert len(product_helpers.get_visible_attributes(new_product)) == 1


def _add_attribute_for_product(product, attr_identifier, attr_type, attr_visibility, attr_name):
    attribute = Attribute.objects.create(
        identifier=attr_identifier, type=attr_type, visibility_mode=attr_visibility, name=attr_name
    )
    product.type.attributes.add(attribute)
    ProductAttribute.objects.create(product=product, attribute=attribute)
