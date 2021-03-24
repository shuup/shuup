# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test.utils import override_settings

from shuup.core.models import ShopProduct
from shuup.testing.factories import (
    get_default_product_type,
    get_default_sales_unit,
    get_default_shop,
    get_default_supplier,
    get_default_tax_class,
)
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
@pytest.mark.parametrize("multiple_suppliers", (True, False))
def test_new_shop_product_suppliers_init(rf, admin_user, multiple_suppliers):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SUPPLIERS=multiple_suppliers):
        shop = get_default_shop()
        supplier = get_default_supplier()
        tax_class = get_default_tax_class()
        product_type = get_default_product_type()
        sales_unit = get_default_sales_unit()

        assert ShopProduct.objects.count() == 0
        client = SmartClient()
        client.login(username="admin", password="password")
        soup = client.soup(reverse("shuup_admin:shop_product.new"))
        supplier_select = soup.find("select", attrs={"name": "shop%s-suppliers" % shop.id})
        assert len(supplier_select.find_all("option")) == (0 if multiple_suppliers else 1)
