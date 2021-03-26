# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import decimal
import pytest

from shuup.core.models import OrderLineType
from shuup.testing.factories import create_product, get_default_supplier

from .test_order_creator import seed_source


@pytest.mark.django_db
def test_order_source_total_gross_weight(rf, admin_user):
    source = seed_source(admin_user)
    supplier = get_default_supplier()
    products_data = [
        {"sku": "sku1234", "net_weight": decimal.Decimal("1"), "gross_weight": decimal.Decimal("43.34257")},
        {"sku": "sku4321", "net_weight": decimal.Decimal("11.342569"), "gross_weight": decimal.Decimal("11.34257")},
        {"sku": "sku1111", "net_weight": decimal.Decimal("0.00"), "gross_weight": decimal.Decimal("0.00")},
    ]

    for product_data in products_data:
        product = create_product(
            sku=product_data.pop("sku"), shop=source.shop, supplier=supplier, default_price=3.33, **product_data
        )
        source.add_line(
            type=OrderLineType.PRODUCT,
            product=product,
            supplier=supplier,
            quantity=1,
            base_unit_price=source.create_price(1),
        )

    assert len(source.get_lines()) == len(products_data)
    assert source.total_gross_weight == sum([data.get("gross_weight") for data in products_data])
