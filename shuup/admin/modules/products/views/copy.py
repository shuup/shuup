# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib import messages
from django.db.transaction import atomic
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView

from shuup.admin.signals import product_copied
from shuup.admin.utils.urls import get_model_url
from shuup.core.models import (
    Product, ProductAttribute, ProductMedia, ShopProduct
)
from shuup.utils.models import get_data_dict


class ProductCopyView(DetailView):
    model = ShopProduct
    context_object_name = "product"

    @atomic()
    def get(self, request, *args, **kwargs):
        shop_product = self.get_object()
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

        new_shop_product = ShopProduct.objects.create(product=new_product, shop=shop_product.shop)
        new_shop_product.visibility = shop_product.visibility
        new_shop_product.purchasable = shop_product.purchasable
        new_shop_product.default_price_value = shop_product.default_price_value
        new_shop_product.primary_category = shop_product.primary_category
        new_shop_product.save()

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

        product_copied.send(sender=type(self), shop=shop_product.shop, copied=product, copy=new_product)
        messages.success(request, _("Product %s copy successfull.") % new_product)
        return HttpResponseRedirect(get_model_url(new_shop_product, shop=self.request.shop))
