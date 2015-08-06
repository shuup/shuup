# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.transaction import atomic

from shoop.admin.form_part import FormPart, TemplatedFormDef, FormPartsViewMixin, SaveFormPartsMixin
from .forms import ProductBaseForm, ShopProductForm, ProductAttributesForm
from shoop.admin.toolbar import URLActionButton, get_default_edit_toolbar

from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import Product, ShopProduct, Shop, ShopStatus, ProductType, TaxClass
from django.utils.translation import ugettext as _


class ProductBaseFormPart(FormPart):
    priority = -1000  # Show this first, no matter what

    def get_form_defs(self):
        yield TemplatedFormDef(
            "base",
            ProductBaseForm,
            template_name="shoop/admin/products/_edit_base_form.jinja",
            required=True,
            kwargs={
                "instance": self.object,
                "languages": settings.LANGUAGES,
                "initial": self.get_initial()
            }
        )

    def form_valid(self, form):
        self.object = form["base"].save()
        return self.object

    def get_initial(self):
        if not self.object.pk:
            # Sane defaults...
            return {
                "type": ProductType.objects.first(),
                "tax_class": TaxClass.objects.first()
            }


class ShopProductFormPart(FormPart):
    priority = -900

    def __init__(self, request, object=None):
        super(ShopProductFormPart, self).__init__(request, object)
        self.shops = Shop.objects.filter(status=ShopStatus.ENABLED)

    def get_shop_instance(self, shop):
        shop_product = self.object.get_shop_instance(shop)
        if not shop_product:
            shop_product = ShopProduct(shop=shop, product=self.object)
        return shop_product

    def get_form_defs(self):
        for shop in self.shops:
            shop_product = self.get_shop_instance(shop)

            yield TemplatedFormDef(
                "shop%d" % shop.pk,
                ShopProductForm,
                template_name="shoop/admin/products/_edit_shop_form.jinja",
                required=False,
                kwargs={"instance": shop_product}
            )

    def form_valid(self, form):
        for shop in self.shops:
            shop_product_form = form["shop%d" % shop.pk]
            if not shop_product_form.changed_data:
                continue
            if not shop_product_form.instance.pk:
                shop_product_form.instance.product = self.object
            inst = shop_product_form.save()
            messages.success(self.request, _("Changes to shop instance for %s saved") % inst.shop)


class ProductAttributeFormPart(FormPart):
    priority = -800

    def get_form_defs(self):
        if not self.object.get_available_attribute_queryset():
            return
        yield TemplatedFormDef(
            "attributes",
            ProductAttributesForm,
            template_name="shoop/admin/products/_edit_attribute_form.jinja",
            required=False,
            kwargs={"product": self.object, "languages": settings.LANGUAGES}
        )

    def form_valid(self, form):
        if "attributes" in form.forms:
            form.forms["attributes"].save()


class ProductEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = Product
    template_name = "shoop/admin/products/edit.jinja"
    context_object_name = "product"
    base_form_part_classes = [ProductBaseFormPart, ShopProductFormPart, ProductAttributeFormPart]
    form_part_class_provide_key = "admin_product_form_part"

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)

    def get_toolbar(self):
        product = self.object
        toolbar = get_default_edit_toolbar(
            self, "product_form",
            delete_url="shoop_admin:product.delete"
        )
        if product.pk:
            toolbar.append(URLActionButton(
                text=_("Manage Media"),
                icon="fa fa-picture-o",
                url=reverse("shoop_admin:product.edit_media", kwargs={"pk": product.pk}),
                extra_css_class="btn-info"
            ))
            toolbar.append(URLActionButton(
                text=_("Manage Cross-Selling"),
                icon="fa fa-exchange",
                url=reverse("shoop_admin:product.edit_cross_sell", kwargs={"pk": product.pk}),
                extra_css_class="btn-info"
            ))
        # TODO: Add extensibility

        return toolbar
