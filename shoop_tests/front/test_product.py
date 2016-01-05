# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.urlresolvers import reverse

from shoop.testing.factories import get_default_product, get_default_shop


@pytest.mark.django_db
def test_product_page(client):
    get_default_shop()
    product = get_default_product()
    response = client.get(
        reverse('shoop:product', kwargs={
            'pk': product.pk,
            'slug': product.slug
            }
        )
    )
    assert b'no such element' not in response.content, 'All items are not rendered correctly'
    # TODO test purchase_multiple and  sales_unit.allow_fractions
