# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest

from shuup.core.models import CategoryStatus
from shuup.testing.browser_utils import initialize_front_browser_test, wait_until_appeared
from shuup.testing.factories import create_product, get_default_category, get_default_shop, get_default_supplier
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


def new_product(i, shop, category):
    supplier = get_default_supplier(shop)
    supplier.stock_managed = False
    supplier.save()
    product = create_product(sku="test%s" % i, shop=shop, name="test%s" % i, supplier=supplier)
    sp = product.get_shop_instance(shop)
    sp.primary_category = category
    sp.save()
    return product


@pytest.mark.django_db
def test_recently_viewed_products(browser, live_server, reindex_catalog):
    shop = get_default_shop()
    category = get_default_category()
    category.shops.add(shop)
    category.status = CategoryStatus.VISIBLE
    category.save()
    category_url = reverse("shuup:category", kwargs={"pk": category.pk, "slug": category.slug})

    products = []
    for i in range(1, 7):
        products.append(new_product(i, shop, category))

    reindex_catalog()

    browser = initialize_front_browser_test(browser, live_server)
    for i, product in enumerate(products, 1):
        product_url = reverse("shuup:product", kwargs={"pk": product.pk, "slug": product.slug})
        browser.visit(live_server + product_url)
        wait_until_appeared(browser, ".product-main")
        browser.visit(live_server + category_url)
        wait_until_appeared(browser, ".categories-nav")
        items = browser.find_by_css(".recently-viewed li")
        assert items.first.text == product.name, "recently clicked product on top"
        assert len(items) == min(i, 5)
