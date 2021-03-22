# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest
import six

from shuup.core.models import AnonymousContact, OrderLineType, Tax
from shuup.core.order_creator import OrderCreator
from shuup.default_tax.models import TaxRule
from shuup.testing.factories import (
    create_package_product,
    create_product,
    get_default_shop,
    get_default_supplier,
    get_default_tax_class,
    get_initial_order_status,
)
from shuup_tests.utils.basketish_order_source import BasketishOrderSource


@pytest.mark.django_db
def test_package_creation():
    package_product = get_package_product()
    assert package_product.sku == "PackageParent"
    assert package_product.is_package_parent()
    assert package_product.get_package_child_to_quantity_map(), "Has children"


def get_package_product():
    """
    :rtype: shuup.core.models.Product
    """
    shop = get_default_shop()
    supplier = get_default_supplier()
    return create_package_product("PackageParent", shop=shop, supplier=supplier)


@pytest.mark.django_db
def test_package_orderability():
    package_product = get_package_product()
    shop = get_default_shop()
    sp = package_product.get_shop_instance(shop)
    supplier = sp.suppliers.get()
    assert not list(sp.get_orderability_errors(supplier=supplier, quantity=1, customer=AnonymousContact()))


@pytest.mark.django_db
def test_repackaging_fails():
    package_product = get_package_product()
    package_def = package_product.get_package_child_to_quantity_map()
    with pytest.raises(ValueError):
        package_product.make_package({})
    with pytest.raises(ValueError):
        package_product.make_package(package_def)


def get_order_source_with_a_package():
    package_product = get_package_product()

    source = BasketishOrderSource(get_default_shop())
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=package_product,
        supplier=get_default_supplier(),
        quantity=10,
        base_unit_price=source.create_price(10),
        sku=package_product.sku,
        text=package_product.name,
    )

    source.status = get_initial_order_status()
    return source


@pytest.mark.django_db
def test_order_creator_can_deal_with_packages():
    source = get_order_source_with_a_package()
    package_product = source.get_lines()[0].product
    package_def = package_product.get_package_child_to_quantity_map()
    creator = OrderCreator()
    order = creator.create_order(source)
    pids_to_quantities = order.get_product_ids_and_quantities()
    for child, quantity in six.iteritems(package_def):
        assert pids_to_quantities[child.pk] == 10 * quantity


@pytest.mark.django_db
def test_order_package_parent_links():
    """
    Test OrderCreator creates package parent links for child lines.
    """
    source = get_order_source_with_a_package()
    order = OrderCreator().create_order(source)

    lines = [prettify_order_line(line) for line in order.lines.all()]
    assert lines == [
        "#0 10 x PackageParent",
        "#1   10 x PackageChild-0, child of #0",
        "#2   20 x PackageChild-1, child of #0",
        "#3   30 x PackageChild-2, child of #0",
        "#4   40 x PackageChild-3, child of #0",
    ]


@pytest.mark.django_db
def test_order_package_children_taxes():
    """
    Test OrderCreator creates package parent links for child lines.
    """
    tax_class = get_default_tax_class()
    tax = Tax.objects.create(rate="0.25", name="Da Tax")
    TaxRule.objects.create(tax=tax).tax_classes.add(tax_class)

    source = get_order_source_with_a_package()
    assert source.get_lines()[0].tax_class == tax_class

    order = OrderCreator().create_order(source)

    lines_and_taxes = []
    for line in order.lines.all():
        lines_and_taxes.append(prettify_order_line(line))
        for line_tax in line.taxes.all():
            lines_and_taxes.append("  %s" % (line_tax,))
    assert lines_and_taxes == [
        "#0 10 x PackageParent",
        "  Da Tax: 20.000000000 EUR on 80.000000000 EUR",
        "#1   10 x PackageChild-0, child of #0",
        "#2   20 x PackageChild-1, child of #0",
        "#3   30 x PackageChild-2, child of #0",
        "#4   40 x PackageChild-3, child of #0",
    ]


@pytest.mark.django_db
def test_order_creator_parent_linkage():
    """
    Test OrderCreator creates parent links from OrderSource.
    """
    source = BasketishOrderSource(get_default_shop())
    source.status = get_initial_order_status()
    source.add_line(
        line_id="LINE1",
        type=OrderLineType.OTHER,
        quantity=1,
        sku="parent",
        text="Parent line",
    )
    source.add_line(
        line_id="LINE1.1",
        parent_line_id="LINE1",
        type=OrderLineType.OTHER,
        quantity=1,
        sku="child1.1",
        text="Child line 1.1",
    )
    source.add_line(
        line_id="LINE1.2",
        parent_line_id="LINE1",
        type=OrderLineType.OTHER,
        quantity=1,
        sku="child1.2",
        text="Child line 1.2",
    )
    source.add_line(
        line_id="LINE1.2.1",
        parent_line_id="LINE1.2",
        type=OrderLineType.OTHER,
        quantity=1,
        sku="child1.2.1",
        text="Child line 1.2.1",
    )
    source.add_line(
        line_id="LINE1.3",
        parent_line_id="LINE1",
        type=OrderLineType.OTHER,
        quantity=1,
        sku="child1.3",
        text="Child line 1.3",
    )
    order = OrderCreator().create_order(source)

    lines = [prettify_order_line(line) for line in order.lines.all()]
    assert lines == [
        "#0 1 x parent",
        "#1   1 x child1.1, child of #0",
        "#2   1 x child1.2, child of #0",
        "#3     1 x child1.2.1, child of #2",
        "#4   1 x child1.3, child of #0",
    ]


def prettify_order_line(line):
    """
    :type line: shuup.core.models.OrderLine
    :rtype: str
    """
    parent = line.parent_line
    parent_info = ", child of #{}".format(parent.ordering) if parent else ""
    return "#{num}{indent} {qty:d} x {sku}{parent_info}".format(
        num=line.ordering,
        indent=("  " * get_line_level(line)),
        qty=int(line.quantity),
        sku=line.sku,
        parent_info=parent_info,
        text=line.text,
    )


def get_line_level(line):
    return (get_line_level(line.parent_line) + 1) if line.parent_line else 0
