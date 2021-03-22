# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings
from django.test.utils import override_settings
from django.utils.translation import activate

from shuup import configuration
from shuup.admin.modules.settings import consts
from shuup.admin.modules.shops.views.edit import ShopBaseForm
from shuup.core.models import ConfigurationItem, Shop, ShopStatus
from shuup.testing.factories import (
    create_product,
    create_random_order,
    create_random_person,
    get_currency,
    get_default_shop,
    get_default_supplier,
)
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient, printable_gibberish
from shuup_tests.utils.forms import get_form_data


@pytest.mark.django_db
def test_protected_fields():
    activate("en")
    shop = Shop.objects.create(
        name="testshop",
        identifier="testshop",
        status=ShopStatus.ENABLED,
        public_name="test shop",
        domain="derp",
        currency="EUR",
    )
    get_currency("EUR")
    get_currency("USD")
    assert shop.name == "testshop"
    assert shop.currency == "EUR"
    assert not ConfigurationItem.objects.filter(shop=shop, key="languages").exists()
    shop_form = ShopBaseForm(instance=shop, languages=settings.LANGUAGES)
    assert not shop_form._get_protected_fields()  # No protected fields just yet, right?
    data = get_form_data(shop_form, prepared=True)
    shop_form = ShopBaseForm(data=data, instance=shop, languages=settings.LANGUAGES)
    _test_cleanliness(shop_form)
    shop_form.save()

    # Now let's make it protected!
    create_product(printable_gibberish(), shop=shop, supplier=get_default_supplier(shop))
    order = create_random_order(customer=create_random_person(), shop=shop)
    assert order.shop == shop

    # And try again...
    data["currency"] = "USD"
    shop_form = ShopBaseForm(data=data, instance=shop, languages=settings.LANGUAGES)
    assert shop_form._get_protected_fields()  # So protected!
    _test_cleanliness(shop_form)
    shop = shop_form.save()
    assert shop.currency == "EUR"  # But the shop form ignored the change . . .


def _test_cleanliness(shop_form):
    shop_form.full_clean()
    assert not shop_form.errors
    assert shop_form.cleaned_data


@pytest.mark.django_db
def test_new_shop(rf, admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        get_default_shop()
        assert Shop.objects.count() == 1

        client = SmartClient()
        client.login(username="admin", password="password")
        client.soup(reverse("shuup_admin:shop.new"))
        payload = {
            "base-public_name__en": "New Shop",
            "base-name__en": "New Shop",
            "base-status": "1",
            "base-currency": "EUR",
            "base-domain": "shop2",
        }
        response = client.post(reverse("shuup_admin:shop.new"), data=payload)
        assert response.status_code == 302
        assert Shop.objects.count() == 2
        shop = Shop.objects.last()
        assert shop.name == "New Shop"
        assert shop.domain == "shop2"


@pytest.mark.django_db
def test_order_configuration(rf, admin_user):
    shop = get_default_shop()
    # clear shop configurations
    ConfigurationItem.objects.filter(shop=shop).delete()
    client = SmartClient()
    client.login(username="admin", password="password")

    url = reverse("shuup_admin:shop.edit", kwargs={"pk": shop.pk})
    response, soup = client.response_and_soup(url)
    assert response.status_code == 200

    length_form_field = "order_configuration-%s" % consts.ORDER_REFERENCE_NUMBER_LENGTH_FIELD
    prefix_form_field = "order_configuration-%s" % consts.ORDER_REFERENCE_NUMBER_PREFIX_FIELD

    length_field = soup.find("input", attrs={"id": "id_%s" % length_form_field})
    prefix_field = soup.find("input", attrs={"id": "id_%s" % prefix_form_field})

    assert length_field
    assert prefix_field

    assert length_field["value"] == str(settings.SHUUP_REFERENCE_NUMBER_LENGTH)  # default value because nothing set yet
    assert "value" not in prefix_field  # field empty

    data = get_base_form_data(shop)
    data[length_form_field] = "18"
    data[prefix_form_field] = "123"
    response, soup = client.response_and_soup(url, data=data, method="post")
    assert "is required" not in soup.prettify()
    assert response.status_code == 302  # redirect after success

    assert configuration.get(shop, consts.ORDER_REFERENCE_NUMBER_LENGTH_FIELD) == 18

    # set global system settings
    # TODO: Enable this before 1.3
    # set_reference_method(rf, admin_user, OrderReferenceNumberMethod.RUNNING)
    data[length_form_field] = "19"
    data[prefix_form_field] = "0"
    client.post(url, data=data)

    assert configuration.get(shop, consts.ORDER_REFERENCE_NUMBER_LENGTH_FIELD) == 19
    assert not configuration.get(
        shop, consts.ORDER_REFERENCE_NUMBER_PREFIX_FIELD
    )  # None because disabled line 104, else 0


def get_base_form_data(shop):
    return {
        "base-public_name__en": shop.public_name,
        "base-name__en": shop.name,
        "base-status": "1",
        "base-currency": shop.currency,
        "product_list_facets-filter_products_by_category_ordering": "1",
        "product_list_facets-filter_products_by_price_ordering": "1",
        "product_list_facets-limit_product_list_page_size_ordering": "1",
        "product_list_facets-sort_products_by_price_ordering": "1",
        "product_list_facets-sort_products_by_name_ordering": "1",
        "product_list_facets-sort_products_by_ascending_created_date_ordering": "1",
        "product_list_facets-sort_products_by_date_created_ordering": "1",
        "product_list_facets-filter_products_by_manufacturer_ordering": "1",
        "product_list_facets-filter_products_by_variation_value_ordering": "1",
    }
