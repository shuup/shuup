# -*- coding: utf-8 -*-
import pytest

from shoop.core.models import Product
from shoop.testing.factories import create_product
from shoop.utils.models import get_in_id_order
from shoop_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_get_in_id_order():
    created_products = [create_product(printable_gibberish()) for x in range(10)]
    ids = [p.pk for p in created_products]
    retrieved_products = get_in_id_order(Product.objects.all(), ids, 5)
    assert [p.pk for p in retrieved_products] == ids[:len(retrieved_products)]
