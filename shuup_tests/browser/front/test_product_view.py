# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest
from django.utils.translation import activate

from shuup.core import cache
from shuup.core.models import ShopProduct
from shuup.testing.browser_utils import initialize_front_browser_test, wait_until_condition
from shuup.testing.factories import create_product, get_default_category, get_default_shop, get_default_supplier
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.django_db
def test_product_descriptions(browser, live_server, reindex_catalog):
    activate("en")
    cache.clear()
    shop = get_default_shop()
    product = create_product(
        "product1",
        shop=shop,
        description="<b>My HTML description</b>",
        short_description="some short of description instead",
        supplier=get_default_supplier(),
    )
    sp = ShopProduct.objects.get(product=product, shop=shop)
    sp.primary_category = get_default_category()
    sp.categories.add(get_default_category())
    sp.save()
    reindex_catalog()

    # initialize test and go to front page
    browser = initialize_front_browser_test(browser, live_server)

    # view product detail page
    url = reverse("shuup:product", kwargs={"pk": product.pk, "slug": product.slug})
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_text_present(product.short_description))
    assert product.description in browser.html

    # product preview
    url = reverse("shuup:all-categories")
    browser.visit("%s%s" % (live_server, url))
    product_div_name = "product-{}".format(product.pk)
    wait_until_condition(browser, lambda x: x.find_by_css("#{} button.btn".format(product_div_name)))
    browser.execute_script("$('#{} button.btn').click();".format(product_div_name))
    assert product.short_description == browser.find_by_css("#{} p.description".format(product_div_name))[0].html
