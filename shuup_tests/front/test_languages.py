# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test.utils import override_settings
from django.utils.translation import activate, get_language

from shuup.core import cache
from shuup.front.utils.translation import get_shop_available_languages, set_shop_available_languages
from shuup.testing import factories
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient


def setup_function(fn):
    cache.clear()


@pytest.mark.django_db
def test_shop_available_languages(admin_user):
    original_language = get_language()
    shop = factories.get_default_shop()
    client = SmartClient()

    with override_settings(
        LANGUAGES=[("it", "Italian"), ("fr", "French"), ("fi", "Finnish"), ("pt", "Portuguese")],
        LANGUAGE_CODE="it",
        PARLER_DEFAULT_LANGUAGE_CODE="it",
    ):
        # there is no language set for the shop, the first one will be used
        response = client.get(reverse("shuup:index"))
        assert get_language() == "it"

        # set an invalid language code
        with pytest.raises(ValueError):
            set_shop_available_languages(shop, ["xpto"])

        # limit the langauges for the shop to "fi" and "pt"
        set_shop_available_languages(shop, ["fi", "pt"])

        # the middleware will automatically set the language to "fi" as that is the first one available for the shop
        response = client.get(reverse("shuup:index"))
        assert get_language() == "fi"

        # the same won't happen for any other url - the middleware will only affect front urls
        client.get("shuup_admin:index")
        assert get_language() == "it"

        # test againt front again
        client.get(reverse("shuup:index"))
        assert get_language() == "fi"

        # again for admin
        client.get("shuup_admin:index")
        assert get_language() == "it"

        # remote all available languages
        set_shop_available_languages(shop, [])
        # this should fallback to settings.LAGUAGE_CODE
        response = client.get(reverse("shuup:index"))
        assert get_language() == "it"

    activate(original_language)


@pytest.mark.django_db
def test_shop_remove_available_languages(admin_user):
    shop = factories.get_default_shop()
    client = SmartClient()

    with override_settings(
        LANGUAGES=[
            ("en", "English"),
            ("fi", "Finnish"),
        ],
        LANGUAGE_CODE="en",
        PARLER_DEFAULT_LANGUAGE_CODE="en",
    ):
        # there is no language set for the shop, the first one will be used
        response = client.get(reverse("shuup:index"))
        assert get_language() == "en"

        # request js catalog file
        response = client.get(reverse("shuup:js-catalog"))
        assert get_language() == "en"

        # when requesting admin js catalog, the language should be any of the available
        client.get("shuup_admin:js-catalog")
        assert get_language() == "en"

        set_shop_available_languages(shop, ["fi"])

        response = client.get(reverse("shuup:index"))
        assert get_language() == "fi"

        response = client.get(reverse("shuup:js-catalog"))
        assert get_language() == "fi"

        client.get("shuup_admin:js-catalog")
        assert get_language() == "en"


@pytest.mark.django_db
def test_admin_set_shop_language(admin_user):
    original_language = get_language()
    shop = factories.get_default_shop()
    client = SmartClient()
    admin_user.set_password("admin")
    admin_user.save()
    client.login(username=admin_user.username, password="admin")

    with override_settings(
        LANGUAGES=[("it", "Italian"), ("fr", "French"), ("fi", "Finnish"), ("pt-br", "Portuguese (Brazil)")],
        LANGUAGE_CODE="it",
        PARLER_DEFAULT_LANGUAGE_CODE="it",
    ):
        assert get_shop_available_languages(shop) == []
        edit_url = reverse("shuup_admin:shop.edit", kwargs=dict(pk=shop.id))
        payload = {
            "translation_config-available_languages": ["pt-br", "fi"],
            "base-public_name__it": shop.public_name,
            "base-name__it": shop.name,
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
            "order_configuration-order_reference_number_length": "20",
            "order_configuration-order_reference_number_prefix": "10",
        }
        response = client.post(edit_url, data=payload)
        assert response.status_code == 302
        assert get_shop_available_languages(shop) == ["pt-br", "fi"]

    activate(original_language)
