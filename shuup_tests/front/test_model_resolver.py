# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.testing import factories
from shuup.utils.django_compat import reverse


@pytest.mark.django_db
def test_category_page(client):
    factories.get_default_shop()
    category = factories.get_default_category()
    response = client.get(reverse("shuup:category", kwargs={"pk": category.pk, "slug": category.slug}))
    assert b"no such element" not in response.content, "All items are not rendered correctly"


@pytest.mark.django_db
def test_resolve_product_url():
    shop = factories.get_default_shop()
    product = factories.create_product("product", shop, factories.get_default_supplier(), "10")
    from shuup.front.template_helpers.urls import model_url

    product_url = reverse("shuup:product", kwargs=dict(pk=product.pk, slug=product.slug))
    assert model_url({}, product) == product_url

    # create a new supplier and use it
    # the URL should still point to the default product URL (no supplier specific)
    # because the given supplier doesn't supplies the product
    supplier2 = factories.get_supplier("", shop)
    assert model_url({}, product, supplier=supplier2) == product_url

    shop_product = product.get_shop_instance(shop)
    shop_product.suppliers.add(supplier2)
    # now the url is supplier2 specific
    product_supplier2_url = reverse(
        "shuup:supplier-product", kwargs=dict(pk=product.pk, slug=product.slug, supplier_pk=supplier2.pk)
    )
    assert model_url({}, product, supplier=supplier2) == product_supplier2_url
