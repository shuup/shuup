import os
import pytest
from django.core.urlresolvers import reverse

from shuup.testing.utils import initialize_front_browser_test
from shuup.testing.factories import (
    create_product, get_default_category, get_default_shop,
    get_default_supplier
)
from shuup.testing.browser_utils import (
    click_element, move_to_element, wait_until_appeared,
    wait_until_disappeared
)
from shuup.core.models import CategoryStatus

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


def new_product(i, shop, category):
    product = create_product(sku="test%s" % i, shop=shop, name="test%s" % i)
    sp = product.get_shop_instance(shop)
    sp.primary_category = category
    sp.save()
    return product


@pytest.mark.browser
@pytest.mark.django_db
def test_recently_viewed_products(browser, live_server, settings):
    shop = get_default_shop()
    category = get_default_category()
    category.shops.add(shop)
    category.status = CategoryStatus.VISIBLE
    category.save()
    category_url = reverse("shuup:category", kwargs={"pk": category.pk, "slug": category.slug})
    browser = initialize_front_browser_test(browser, live_server)
    for i in range(1, 7):
        product = new_product(i, shop, category)
        product_url = reverse("shuup:product", kwargs={"pk": product.pk, "slug": product.slug})
        browser.visit(live_server + product_url)
        wait_until_appeared(browser, ".product-main")
        browser.visit(live_server + category_url)
        wait_until_appeared(browser, ".categories-nav")
        items = browser.find_by_css(".recently-viewed li")
        assert items.first.text == product.name, "recently clicked product on top"
        assert len(items) == min(i, 5)
