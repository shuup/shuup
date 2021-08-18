# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import transaction
from django.db.transaction import atomic

from shuup.admin.signals import product_copied
from shuup.core.models import Product, ProductAttribute, ProductMedia, Shop, ShopProduct, Supplier
from shuup.core.tasks import run_task
from shuup.utils.models import copy_model_instance, get_data_dict


class ProductCloner:
    def __init__(self, current_shop: Shop, current_supplier: Supplier = None):
        self.current_shop = current_shop
        self.current_supplier = current_supplier

    @atomic()
    def clone_product(self, shop_product: ShopProduct):
        # clone product
        product = shop_product.product
        new_product = copy_model_instance(product)
        new_product.sku = "{}-{}".format(product.sku, Product.objects.count())
        new_product.name = ("{name} - Copy").format(name=product.name)
        new_product.save()

        for trans in product.translations.all():
            trans_product_data = get_data_dict(trans)
            trans_product_data["master"] = new_product
            new_trans = Product._parler_meta.get_model_by_related_name("translations").objects.get_or_create(
                language_code=trans.language_code, master=new_product
            )[0]
            for (key, value) in trans_product_data.items():
                setattr(new_trans, key, value)

            new_trans.save()

        # clone shop product
        new_shop_product = copy_model_instance(shop_product)
        new_shop_product.product = new_product
        new_shop_product.save()

        for trans in shop_product.translations.all():
            trans_shop_product_data = get_data_dict(trans)
            trans_shop_product_data["master"] = new_shop_product
            ShopProduct._parler_meta.get_model_by_related_name("translations").objects.get_or_create(
                **trans_shop_product_data
            )

        # clone suppliers
        if self.current_supplier:
            new_shop_product.suppliers.add(self.current_supplier)
        else:
            new_shop_product.suppliers.set(shop_product.suppliers.all())

        new_shop_product.categories.set(shop_product.categories.all())

        # clone attributes
        for original_product_attribute in product.attributes.all():
            product_attribute = ProductAttribute.objects.create(
                product=new_product,
                attribute=original_product_attribute.attribute,
            )
            product_attribute.value = original_product_attribute.value
            product_attribute.save()

        # clone media
        for media in product.media.all():
            media_copy = copy_model_instance(media)
            media_copy.product = new_product
            media_copy.file = media.file
            media.shops.add(shop_product.shop)
            if product.primary_image == media:
                new_product.primary_image = media_copy

            for trans in media.translations.all():
                trans_product_media_data = get_data_dict(trans)
                trans_product_media_data["master"] = new_shop_product
                ProductMedia._parler_meta.get_model_by_related_name("translations").objects.create(
                    **trans_product_media_data
                )
            media_copy.save()

        product_copied.send(
            sender=type(self), shop=shop_product.shop, supplier=self.current_supplier, copied=product, copy=new_product
        )

        transaction.on_commit(
            lambda: run_task("shuup.core.catalog.tasks.index_shop_product", shop_product_id=new_product.pk)
        )

        return new_shop_product
