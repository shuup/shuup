# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal
import os
import random

import factory.fuzzy as fuzzy
from django.conf import settings
from PIL import Image
from six import BytesIO

from shuup.core.models import (
    Category, CategoryStatus, PersonContact, Product, ProductMedia,
    ProductMediaKind, SalesUnit, Shop, ShopProduct, ShopProductVisibility
)
from shuup.testing.factories import (
    get_default_product_type, get_default_supplier, get_default_tax_class
)
from shuup.utils.filer import filer_image_from_data


def create_sample_category(name, description, business_segment, image_file_path, shop):
    category = Category.objects.create(
        name=name,
        description=description,
        status=CategoryStatus.VISIBLE
    )

    _, full_file_name = os.path.split(image_file_path)
    file_name, _ = os.path.splitext(full_file_name)
    image = Image.open(image_file_path)
    sio = BytesIO()
    image.save(sio, format="JPEG")

    filer_image = filer_image_from_data(
        request=None,
        path="ProductCategories/Samples/%s" % business_segment.capitalize(),
        file_name="{}.jpeg".format(file_name),
        file_data=sio.getvalue(),
        sha1=True
    )

    category.image = filer_image
    category.shops.add(shop)
    category.save()
    return category


def create_sample_product(name, description, business_segment, image_file_path, shop):
    product = Product.objects.create(
        name=name,
        description=description,
        type=get_default_product_type(),
        tax_class=get_default_tax_class(),
        sales_unit=SalesUnit.objects.first(),
        sku=fuzzy.FuzzyText(length=10).fuzz()
    )

    _, full_file_name = os.path.split(image_file_path)
    file_name, _ = os.path.splitext(full_file_name)
    image = Image.open(image_file_path)
    sio = BytesIO()
    image.save(sio, format="JPEG")

    filer_image = filer_image_from_data(
        request=None,
        path="ProductImages/Samples/%s" % business_segment.capitalize(),
        file_name="{}.jpeg".format(file_name),
        file_data=sio.getvalue(),
        sha1=True
    )

    media = ProductMedia.objects.create(
        product=product,
        kind=ProductMediaKind.IMAGE,
        file=filer_image
    )
    media.shops = Shop.objects.all()
    media.save()
    product.primary_image = media
    product.save()

    sp = ShopProduct.objects.create(
        product=product,
        purchasable=True,
        visibility=ShopProductVisibility.ALWAYS_VISIBLE,
        default_price_value=decimal.Decimal(random.random() * random.randrange(0, 500)),
        shop=shop,
        shop_primary_image=media
    )
    sp.categories = shop.categories.all()
    sp.suppliers.add(get_default_supplier())

    # configure prices
    if "shuup.customer_group_pricing" in settings.INSTALLED_APPS:
        from shuup.customer_group_pricing.models import CgpPrice
        CgpPrice.objects.create(
            product=product,
            price_value=random.randint(15, 340),
            shop=shop,
            group=PersonContact.get_default_group()
        )

    return product
