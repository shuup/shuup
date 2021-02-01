# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.db.transaction import atomic
from django.forms.formsets import DEFAULT_MAX_NUM, DEFAULT_MIN_NUM
from django.forms.models import BaseModelFormSet
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView, View
from filer.models import File

from shuup.admin.base import MenuEntry
from shuup.admin.forms.widgets import MediaChoiceWidget
from shuup.admin.toolbar import PostActionButton, Toolbar
from shuup.admin.utils.urls import get_model_url
from shuup.core.models import (
    Product, ProductMedia, ProductMediaKind, Shop, ShopProduct
)
from shuup.utils.django_compat import force_text
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


class ProductMediaForm(MultiLanguageModelForm):
    class Meta:
        model = ProductMedia
        fields = (
            "shops",
            "kind",
            "file",
            "external_url",
            "ordering",
            "enabled",
            "public",
            "purchased",
            "title",
            "description"
        )

    def __init__(self, **kwargs):
        self.product = kwargs.pop("product")
        super(ProductMediaForm, self).__init__(**kwargs)
        # Filer has a misimplemented field; we need to do this manually.
        self.fields["file"].widget = MediaChoiceWidget()

    def pre_master_save(self, instance):
        instance.product = self.product


class ProductMediaFormSet(BaseModelFormSet):
    validate_min = False
    min_num = DEFAULT_MIN_NUM
    validate_max = False
    max_num = DEFAULT_MAX_NUM
    absolute_max = DEFAULT_MAX_NUM
    model = ProductMedia
    can_delete = True
    can_order = False
    extra = 5

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop("product")
        super(ProductMediaFormSet, self).__init__(*args, **kwargs)

    def form(self, **kwargs):
        kwargs.setdefault("languages", settings.LANGUAGES)
        kwargs.setdefault("product", self.product)
        return ProductMediaForm(**kwargs)


class ProductMediaEditView(UpdateView):
    """
    A view for editing all the media for a product, including attachments
    that are not just images.

    Currently sort of utilitarian and confusing.
    """
    model = Product
    template_name = "shuup/admin/products/edit_media.jinja"
    context_object_name = "product"
    form_class = ProductMediaFormSet

    def get_breadcrumb_parents(self):
        return [
            MenuEntry(
                text="%s" % self.object,
                url=get_model_url(self.object, shop=self.request.shop)
            )
        ]

    def get_object(self, queryset=None):
        if not self.kwargs.get(self.pk_url_kwarg):
            return self.model()
        # modify kwargs to match the product instead
        # TODO: Change this to use ShopProduct
        key = self.pk_url_kwarg
        self.kwargs[key] = ShopProduct.objects.get(pk=self.kwargs[key]).product.pk
        return super(ProductMediaEditView, self).get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super(ProductMediaEditView, self).get_context_data(**kwargs)
        context["title"] = _("Edit Media: %s") % self.object
        context["toolbar"] = Toolbar([
            PostActionButton(
                icon="fa fa-save",
                form_id="media_form",
                text=_("Save"),
                extra_css_class="btn-success",
            ),
        ], view=self)
        return context

    def get_form_kwargs(self):
        kwargs = super(ProductMediaEditView, self).get_form_kwargs()
        instance = kwargs.pop("instance", None)
        kwargs["queryset"] = ProductMedia.objects.filter(product=instance).order_by("ordering")
        kwargs["product"] = instance
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Changes were saved."))
        return HttpResponseRedirect(self.request.path)


class ProductMediaBulkAdderView(View):
    """
    Adds media in bulk to a pre-existing product.
    """
    @atomic
    def post(self, *args, **kwargs):
        ids = self.request.POST.getlist("file_ids")
        shop_product_id = kwargs.pop("pk")
        kind = self.request.POST.get("kind")
        shop = self.request.shop
        shop_id = self.request.POST.get("shop_id", shop.pk)
        if not ids or not shop_product_id:
            return JsonResponse({"response": "error", "message": "Error! Bad request."}, status=400)
        if not Shop.objects.filter(pk=shop_id).exists():
            return JsonResponse({"response": "error", "message": "Error! Invalid shop id `%s`." % shop_id}, status=400)

        shop_product = ShopProduct.objects.filter(pk=shop_product_id, shop_id=shop_id).first()
        if not shop_product:
            return JsonResponse(
                {"response": "error", "message": "Error! Invalid shop product id `%s`." % shop_product_id}, status=400)
        if kind == "images":
            kind = ProductMediaKind.IMAGE
        elif kind == "media":
            kind = ProductMediaKind.GENERIC_FILE
        else:
            return JsonResponse({"response": "error", "message": "Error! Invalid file kind `%s`." % kind}, status=400)
        for file_id in ids:
            if not File.objects.filter(id=file_id).exists():
                return JsonResponse(
                    {"response": "error", "message": "Error! Invalid file id `%s`." % file_id}, status=400
                )

        added = []

        for file_id in ids:
            if not ProductMedia.objects.filter(
                    product_id=shop_product.product_id,
                    file_id=file_id,
                    kind=kind,
                    shops__in=[shop_id]).exists():
                image = ProductMedia.objects.create(
                    product_id=shop_product.product_id,
                    file_id=file_id,
                    kind=kind,
                )
                image.shops.add(shop_id)
                added.append({
                    "product": image.product_id,
                    "file": int(file_id),
                    "kind": kind.value,
                    "product_media": image.pk
                })
        return JsonResponse({
            "response": "success",
            "added": added,
            "message": force_text(_("Files added to the product."))
        })
