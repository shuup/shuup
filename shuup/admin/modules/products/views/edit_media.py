# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.forms.formsets import DEFAULT_MAX_NUM, DEFAULT_MIN_NUM
from django.forms.models import BaseModelFormSet
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView

from shuup.admin.base import MenuEntry
from shuup.admin.forms.widgets import MediaChoiceWidget
from shuup.admin.toolbar import PostActionButton, Toolbar
from shuup.admin.utils.urls import get_model_url
from shuup.core.models import Product, ProductMedia
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
                url=get_model_url(self.object)
            )
        ]

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
        ])
        return context

    def get_form_kwargs(self):
        kwargs = super(ProductMediaEditView, self).get_form_kwargs()
        instance = kwargs.pop("instance", None)
        kwargs["queryset"] = ProductMedia.objects.filter(product=instance).order_by("ordering")
        kwargs["product"] = instance
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Changes saved."))
        return HttpResponseRedirect(self.request.path)
