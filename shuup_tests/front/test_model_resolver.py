# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from shuup.utils.django_compat import reverse

from shuup.testing import factories


@pytest.mark.django_db
def test_category_page(client):
    factories.get_default_shop()
    category = factories.get_default_category()
    response = client.get(reverse('shuup:category', kwargs={'pk': category.pk, 'slug': category.slug}))
    assert b'no such element' not in response.content, 'All items are not rendered correctly'


@pytest.mark.django_db
def test_resolve_product_url():
    shop = factories.get_default_shop()
    product = factories.create_product("product", shop, factories.get_default_supplier(), "10")
    from shuup.front.template_helpers.urls import model_url
    assert model_url({}, product) == reverse("shuup:product", kwargs=dict(pk=product.pk, slug=product.slug))
