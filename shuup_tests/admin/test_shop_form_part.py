# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup

from shuup import configuration
from shuup.admin.modules.shops.views.edit import ShopEditView
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_multiple_images_shop_form_part(admin_user, rf):
    shop = factories.get_default_shop()

    get_request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = ShopEditView.as_view()(get_request, pk=shop.pk)
    assert response.status_code == 200
    response.render()
    soup = BeautifulSoup(response.content)
    assert soup.find_all("input", attrs={"id": "id_test_shop_form_part-images"})

    # set inside shuup/testing/admin_module/form_parts.py
    assert configuration.get(shop, "multiple_images_ids") is None

    # save 3 images
    image1 = factories.get_random_filer_image()
    image2 = factories.get_random_filer_image()
    image3 = factories.get_random_filer_image()

    payload = {
        "base-name__en": "Default",
        "base-public_name__en": "Default",
        "base-domain": "default.shuup.com",
        "base-description__en": "",
        "base-status": "1",
        "base-currency": "EUR",
        "base-staff_members": [],
        "base-labels": [],
        "address-country": [],
        "translation_config-available_languages": "en",
        "order_configuration-order_reference_number_length": "17",
        "order_configuration-order_reference_number_prefix": "",
        "test_shop_form_part-images": "{};{};{}".format(image1.pk, image2.pk, image3.pk)
    }

    post_request = apply_request_middleware(rf.post("/", data=payload), user=admin_user)
    response = ShopEditView.as_view()(post_request, pk=shop.pk)
    assert response.status_code == 302
    response = ShopEditView.as_view()(get_request, pk=shop.pk)
    assert response.status_code == 200
    response.render()
    soup = BeautifulSoup(response.content)
    assert soup.find_all("input", attrs={"id": "id_test_shop_form_part-images"})[0].attrs["value"] == "{};{};{}".format(image1.pk, image2.pk, image3.pk)
    assert configuration.get(shop, "multiple_images_ids") == [image1.pk, image2.pk, image3.pk]

    # remove images
    payload["test_shop_form_part-images"] = ""

    post_request = apply_request_middleware(rf.post("/", data=payload), user=admin_user)
    response = ShopEditView.as_view()(post_request, pk=shop.pk)
    assert response.status_code == 302
    response = ShopEditView.as_view()(get_request, pk=shop.pk)
    assert response.status_code == 200
    response.render()
    soup = BeautifulSoup(response.content)
    assert not soup.find_all("input", attrs={"id": "id_test_shop_form_part-images"})[0].attrs.get("value")
    assert configuration.get(shop, "multiple_images_ids") == []
