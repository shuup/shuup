# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from collections import Counter
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models.signals import m2m_changed, post_save
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry, SearchResult
from shuup.admin.menu import PRODUCTS_MENU_CATEGORY
from shuup.admin.modules.products.signal_handlers import update_categories_post_save, update_categories_through
from shuup.admin.utils.search import split_query
from shuup.admin.utils.urls import (
    admin_url,
    derive_model_url,
    get_edit_and_list_urls,
    get_model_url,
    manipulate_query_string,
)
from shuup.admin.views.home import HelpBlockCategory, SimpleHelpBlock
from shuup.core.models import Product, ShopProduct
from shuup.utils.django_compat import force_text, reverse


class ProductModule(AdminModule):
    name = _("Products")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:shop_product.list")

    def get_urls(self):
        return [
            admin_url(
                r"^products/(?P<pk>\d+)/delete/$",
                "shuup.admin.modules.products.views.ProductDeleteView",
                name="shop_product.delete",
            ),
            admin_url(
                r"^products/(?P<pk>\d+)/media/$",
                "shuup.admin.modules.products.views.ProductMediaEditView",
                name="shop_product.edit_media",
            ),
            admin_url(
                r"^products/(?P<pk>\d+)/media/add/$",
                "shuup.admin.modules.products.views.ProductMediaBulkAdderView",
                name="shop_product.add_media",
            ),
            admin_url(
                r"^products/(?P<pk>\d+)/crosssell/$",
                "shuup.admin.modules.products.views.ProductCrossSellEditView",
                name="shop_product.edit_cross_sell",
            ),
            admin_url(
                r"^products/(?P<pk>\d+)/package/$",
                "shuup.admin.modules.products.views.ProductPackageView",
                name="shop_product.edit_package",
            ),
            admin_url(
                r"^products/mass-edit/$",
                "shuup.admin.modules.products.views.ProductMassEditView",
                name="shop_product.mass_edit",
            ),
            admin_url(
                r"^products/(?P<pk>\d+)/copy/$",
                "shuup.admin.modules.products.views.copy.ProductCopyView",
                name="shop_product.copy",
            ),
        ] + get_edit_and_list_urls(
            url_prefix="^products",
            view_template="shuup.admin.modules.products.views.Product%sView",
            name_template="shop_product.%s",
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Products"),
                icon="fa fa-cube",
                url="shuup_admin:shop_product.list",
                category=PRODUCTS_MENU_CATEGORY,
                ordering=1,
            )
        ]

    def get_search_results(self, request, query):
        shop = request.shop
        minimum_query_length = 3
        skus_seen = set()
        if len(query) >= minimum_query_length:
            pk_counter = Counter()
            pk_counter.update(Product.objects.filter(sku__startswith=query).values_list("pk", flat=True))
            name_q = Q()
            for part in split_query(query, minimum_query_length):
                name_q &= Q(name__icontains=part)
            pk_counter.update(
                Product._parler_meta.root_model.objects.filter(name_q).values_list("master_id", flat=True)
            )
            pks = [pk for (pk, count) in pk_counter.most_common(10)]

            for product in Product.objects.filter(pk__in=pks, shop_products__shop_id=shop.id):
                relevance = 100 - pk_counter.get(product.pk, 0)
                skus_seen.add(product.sku.lower())
                yield SearchResult(
                    text=force_text(product),
                    url=get_model_url(product, shop=request.shop),
                    category=_("Products"),
                    relevance=relevance,
                )

        if len(query) >= minimum_query_length:
            url = reverse("shuup_admin:shop_product.new")
            if " " in query:
                yield SearchResult(
                    text=_('Create Product Called "%s"') % query,
                    url=manipulate_query_string(url, name=query),
                    is_action=True,
                )
            else:
                if query.lower() not in skus_seen:
                    yield SearchResult(
                        text=_('Create Product with SKU "%s"') % query,
                        url=manipulate_query_string(url, sku=query),
                        is_action=True,
                    )

    def get_help_blocks(self, request, kind):
        actions = []

        from shuup.admin.utils.permissions import has_permission

        if has_permission(request.user, "shop_product.new"):
            actions.append({"text": _("New product"), "url": self.get_model_url(ShopProduct, "new")})
        if "shuup.importer" in settings.INSTALLED_APPS and has_permission(request.user, "importer.import"):
            actions.append({"text": _("Import"), "url": reverse("shuup_admin:importer.import")})

        if actions:
            yield SimpleHelpBlock(
                text=_("Add a product to see it in your store"),
                actions=actions,
                icon_url="shuup_admin/img/product.png",
                priority=0,
                category=HelpBlockCategory.PRODUCTS,
                done=Product.objects.filter(shop_products__shop=request.shop).exists() if kind == "setup" else False,
            )

    def get_model_url(self, object, kind, shop=None):
        if isinstance(object, Product):
            try:
                if not shop:
                    shop = object.shop_products.first().shop
                object = object.get_shop_instance(shop)
            except ObjectDoesNotExist:
                return None
        return derive_model_url(ShopProduct, "shuup_admin:shop_product", object, kind)


m2m_changed.connect(
    update_categories_through,
    sender=ShopProduct.categories.through,
    dispatch_uid="shop_product:update_categories_through",
)


post_save.connect(update_categories_post_save, sender=ShopProduct, dispatch_uid="shop_product:update_categories")
