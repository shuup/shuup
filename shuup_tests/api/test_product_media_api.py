# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import base64
import json
import os

from rest_framework import status
from rest_framework.test import APIClient

from shuup.core.models import ProductMedia, ProductMediaKind
from shuup.testing.factories import (
    create_product, get_default_shop, get_random_filer_image
)


def test_send_product_media_image(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    product = create_product("product", shop=shop)

    image = get_random_filer_image()
    with open(image.path, 'rb') as f:
        img_base64 = base64.b64encode(f.read()).decode()
        uri = "data:image/jpeg;base64,{}".format(img_base64)

    media_data = {
        "translations": {
            "en": {
                "title": "My image title",
                "description": "My image description"
            }
        },
        "shops": [shop.pk],
        "kind": ProductMediaKind.IMAGE.value,
        "file": uri,
        "path": "/what/the/folder"
    }
    response = client.post("/api/shuup/product/%d/add_media/" % product.pk,
                           content_type="application/json",
                           data=json.dumps(media_data))
    assert response.status_code == status.HTTP_201_CREATED
    assert product.media.count() == 1
    product_media = product.media.first()
    assert product_media.title == media_data["translations"]["en"]["title"]
    assert product_media.description == media_data["translations"]["en"]["description"]
    assert product_media.shops.count() == len(media_data["shops"])
    assert set(product_media.shops.all().values_list("pk", flat=True)) >= set(media_data["shops"])
    assert product_media.kind.value == media_data["kind"]
    assert product_media.file.folder.pretty_logical_path == media_data["path"]
    with open(product_media.file.path, 'rb') as f:
        assert img_base64 == base64.b64encode(f.read()).decode()


def test_send_product_media_url(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    product = create_product("product", shop=shop)

    media_data = {
        "translations": {
            "en": {
                "title": "My image title",
                "description": "My image description"
            }
        },
        "shops": [shop.pk],
        "kind": ProductMediaKind.IMAGE.value,
        "external_url": "http://www.goodimages.com/a-good-image.jpg",
    }
    response = client.post("/api/shuup/product/%d/add_media/" % product.pk,
                           content_type="application/json",
                           data=json.dumps(media_data))
    assert response.status_code == status.HTTP_201_CREATED
    assert product.media.count() == 1
    product_media = product.media.first()
    assert product_media.title == media_data["translations"]["en"]["title"]
    assert product_media.description == media_data["translations"]["en"]["description"]
    assert product_media.shops.count() == len(media_data["shops"])
    assert set(product_media.shops.all().values_list("pk", flat=True)) >= set(media_data["shops"])
    assert product_media.kind.value == media_data["kind"]
    assert product_media.external_url == media_data["external_url"]


def test_send_product_media_erros(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    product = create_product("product", shop=shop)

    media_data = {
        "translations": {
            "en": {"title": "My image title", "description": "My image description"}
        },
        "shops": [shop.pk],
        "kind": ProductMediaKind.IMAGE.value
    }

    # do not set file or external_url
    response = client.post("/api/shuup/product/%d/add_media/" % product.pk,
                           content_type="application/json",
                           data=json.dumps(media_data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = json.loads(response.content.decode("utf-8"))
    assert "You may set either `file` or `external_url`." in response_data["non_field_errors"]

    # do not set path for file
    image = get_random_filer_image()
    with open(image.path, 'rb') as f:
        img_base64 = base64.b64encode(os.urandom(50)).decode()
        uri = "data:application/octet-stream;base64,{}".format(img_base64)

    media_data = {
        "translations": {
            "en": {"title": "My image title", "description": "My image description"}
        },
        "shops": [shop.pk],
        "kind": ProductMediaKind.IMAGE.value,
        "file": uri
    }
    response = client.post("/api/shuup/product/%d/add_media/" % product.pk,
                           content_type="application/json",
                           data=json.dumps(media_data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = json.loads(response.content.decode("utf-8"))
    assert "`path` is required when `file` is set." in response_data["non_field_errors"]


def test_send_product_media_file(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    product = create_product("product", shop=shop)

    image = get_random_filer_image()
    with open(image.path, 'rb') as f:
        img_base64 = base64.b64encode(os.urandom(50)).decode()
        uri = "data:application/octet-stream;base64,{}".format(img_base64)

    media_data = {
        "translations": {
            "en": {
                "title": "My octet file",
                "description": "May destroy your server!"
            }
        },
        "shops": [shop.pk],
        "kind": ProductMediaKind.IMAGE.value,
        "file": uri,
        "path": "/what/the/folderzzz"
    }
    response = client.post("/api/shuup/product/%d/add_media/" % product.pk,
                           content_type="application/json",
                           data=json.dumps(media_data))
    assert response.status_code == status.HTTP_201_CREATED
    assert product.media.count() == 1
    product_media = product.media.first()
    assert product_media.title == media_data["translations"]["en"]["title"]
    assert product_media.description == media_data["translations"]["en"]["description"]
    assert product_media.shops.count() == len(media_data["shops"])
    assert set(product_media.shops.all().values_list("pk", flat=True)) >= set(media_data["shops"])
    assert product_media.kind.value == media_data["kind"]
    assert product_media.file.folder.pretty_logical_path == media_data["path"]
    with open(product_media.file.path, 'rb') as f:
        assert img_base64 == base64.b64encode(f.read()).decode()


def test_product_media_api(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    product = create_product("product", shop=shop)

    # create 2 images for product, 1 with contents, other with external url
    image = get_random_filer_image()
    media = ProductMedia.objects.create(product=product,
                                        kind=ProductMediaKind.IMAGE, file=image, enabled=True, public=True)
    media_external = ProductMedia.objects.create(product=product,
                                                 kind=ProductMediaKind.IMAGE,
                                                 external_url="http://www.myimage.com/img.gif",
                                                 enabled=True, public=True)
    product.primary_image = media
    product.save()

    # get product media
    response = client.get("/api/shuup/product_media/%d/" % media.pk)
    media_data = json.loads(response.content.decode("utf-8"))
    assert media_data["kind"] == media.kind.value
    assert media_data["product"] == product.pk
    assert media_data["public"] == media.public
    assert media_data["id"] == media.pk

    # get external media
    response = client.get("/api/shuup/product_media/%d/" % media_external.pk)
    media_data = json.loads(response.content.decode("utf-8"))
    assert media_data["kind"] == media_external.kind.value
    assert media_data["product"] == product.pk
    assert media_data["public"] == media_external.public
    assert media_data["id"] == media_external.pk
    assert media_data["external_url"] == media_external.external_url

    # update product media
    image = get_random_filer_image()
    with open(image.path, 'rb') as f:
        img_base64 = base64.b64encode(os.urandom(50)).decode()
        uri = "data:application/octet-stream;base64,{}".format(img_base64)

    media_data = {
        "translations": {
            "en": {"title": "title 2", "description": "desc2"}
        },
        "shops": [shop.pk],
        "kind": ProductMediaKind.IMAGE.value,
        "file": uri,
        "path": "/what/the/zzzz"
    }
    response = client.put("/api/shuup/product_media/%d/" % media.pk,
                          content_type="application/json",
                          data=json.dumps(media_data))
    assert response.status_code == status.HTTP_200_OK
    media.refresh_from_db()
    assert media.title == media_data["translations"]["en"]["title"]
    assert media.description == media_data["translations"]["en"]["description"]
    assert media.shops.count() == len(media_data["shops"])
    assert set(media.shops.all().values_list("pk", flat=True)) >= set(media_data["shops"])
    assert media.kind.value == media_data["kind"]
    assert media.file.folder.pretty_logical_path == media_data["path"]
    with open(media.file.path, 'rb') as f:
        assert img_base64 == base64.b64encode(f.read()).decode()

    media_count = product.media.count()
    # deletes an image
    response = client.delete("/api/shuup/product_media/%d/" % media.pk)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert media_count-1 == product.media.count()


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
