# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from shuup.core.models import ProductMode, ProductVariationVariable, ProductVariationVariableValue
from shuup.testing.factories import create_product, get_default_shop
from shuup.utils.django_compat import reverse
from shuup_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_variation_redirect(client):
    """
    view should redirect from child url to parent url
    with selected variation as param
    """
    shop = get_default_shop()
    parent = create_product(printable_gibberish(), shop)
    child = create_product(printable_gibberish(), shop)

    children_url = reverse("shuup:product", kwargs=dict(pk=child.pk, slug=child.slug))
    response = client.get(children_url)
    assert response.status_code == 200

    child.link_to_parent(parent)

    parent_url = reverse("shuup:product", kwargs=dict(pk=parent.pk, slug=parent.slug))
    response = client.get(parent_url)
    assert response.status_code == 200

    response = client.get(children_url, follow=True)
    assert response.status_code == 200

    last_url, status_code = response.redirect_chain[-1]
    assert status_code == 302

    expected_url = "{}?variation={}".format(
        reverse("shuup:product", kwargs=dict(pk=parent.pk, slug=parent.slug)), child.sku
    )
    if last_url.startswith("http"):
        assert last_url.endswith(expected_url)
    else:
        assert last_url == expected_url


@pytest.mark.django_db
def test_variation_detail_view(client):
    shop = get_default_shop()

    parent = create_product(printable_gibberish(), shop)

    assert parent.mode == ProductMode.NORMAL

    volume = ProductVariationVariable.objects.create(
        identifier="volume",
        name="volume",
        product=parent,
        ordering=0,
    )
    for index, value in enumerate(["1ml", "2ml", "3ml"]):
        ProductVariationVariableValue.objects.create(
            identifier=value,
            value=value,
            variable=volume,
            ordering=index,
        )

    color = ProductVariationVariable.objects.create(
        identifier="color",
        name="color",
        product=parent,
        ordering=1,
    )
    for index, value in enumerate(["red", "green", "blue"]):
        ProductVariationVariableValue.objects.create(
            identifier=value,
            value=value,
            variable=color,
            ordering=index,
        )

    child = create_product(printable_gibberish(), shop)

    values = [volume.values.all()[1], color.values.all()[1]]
    assert child.link_to_parent(
        parent,
        variables={
            volume: values[0],
            color: values[1],
        },
    )

    assert parent.mode == ProductMode.VARIABLE_VARIATION_PARENT

    variation_url = "{}?variation={}".format(
        reverse("shuup:product", kwargs=dict(pk=parent.pk, slug=parent.slug)), child.sku
    )
    response = client.get(variation_url + "BAD_VARIATION_SKU")
    assert response.status_code == 404

    response = client.get(variation_url)
    assert response.status_code == 200

    assert response.context_data["shop_product"]

    assert response.context_data["selected_variation"] == child
    assert response.context_data["selected_variation_values"] == [v.pk for v in values]
