# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.http import HttpResponseRedirect
from django.db.transaction import atomic
from django.contrib import messages

from shuup.core.models import (
    Product, ProductAttribute, ProductMedia, ShopProduct
)
from shuup.admin.signals import product_copied
from shuup.utils.models import get_data_dict

class ProductCloner():
    def __init__(self, current_shop, current_supplier):
        self.current_shop = current_shop
        self.current_supplier = current_supplier
    
    @atomic
    def clone_product(self, shop_product=None):
        product = shop_product.product
        product_data = get_data_dict(product)
        product_data.update({
            "sku": "{}-{}".format(product.sku, Product.objects.count())
        })
        new_product = Product.objects.create(**product_data)
        new_product.name = product.name
        new_product.short_description = product.short_description
        new_product.description = product.description
        new_product.slug = product.slug
        new_product.save()

        new_shop_product = ShopProduct.objects.create(product=new_product, shop=self.current_shop)
        new_shop_product.visibility = shop_product.visibility
        new_shop_product.purchasable = shop_product.purchasable
        new_shop_product.default_price_value = shop_product.default_price_value
        new_shop_product.primary_category = shop_product.primary_category
        new_shop_product.save()

        if self.current_supplier:
            new_shop_product.suppliers.add(self.current_supplier)
        else:
            new_shop_product.suppliers.set(shop_product.suppliers.all())
            
        new_shop_product.categories.set(shop_product.categories.all())

        for attribute in product.attributes.all():
            ProductAttribute.objects.create(product=new_product, attribute=attribute.attribute, value=attribute.value)

        for old_media in product.media.all():
            media = ProductMedia.objects.create(product=new_product, file=old_media.file, kind=old_media.kind)
            media.shops.add(shop_product.shop)
            if product.primary_image == old_media:
                new_product.primary_image = media
                new_product.save()

        product_copied.send(sender=type(self), shop=shop_product.shop, supplier=self.current_supplier, copied=product, copy=new_product)

        return new_shop_product
