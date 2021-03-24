# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView

from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.picotable import Column, TextFilter
from shuup.admin.utils.views import CreateOrUpdateView, PicotableListView
from shuup.discounts.models import CouponCode, Discount
from shuup.utils.django_compat import force_text, reverse_lazy


class CouponCodeListView(PicotableListView):
    model = CouponCode
    url_identifier = "discounts_coupon_codes"

    default_columns = [
        Column(
            "code",
            _("Code"),
            sort_field="code",
            display="code",
            linked=True,
            filter_config=TextFilter(operator="startswith"),
        ),
        Column("usages", _("Usages"), display="get_usages"),
        Column("usage_limit_customer", _("Usages Limit per contact")),
        Column("usage_limit", _("Usage Limit")),
        Column("active", _("Active")),
        Column("created_by", _("Created by")),
        Column("created_on", _("Date created")),
    ]

    def get_usages(self, instance, *args, **kwargs):
        return instance.usages.count()

    def get_queryset(self):
        return CouponCode.objects.filter(shops=get_shop(self.request))


class CouponCodeForm(forms.ModelForm):
    class Meta:
        model = CouponCode
        exclude = ("shops", "created_by", "modified_by")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.shop = get_shop(self.request)
        super(CouponCodeForm, self).__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields["coupon_code_discounts"] = Select2MultipleField(
                label=_("Product Discounts"),
                help_text=_("Select discounts linked to this coupon code."),
                model=Discount,
                required=False,
            )
            initial_discounts = self.instance.coupon_code_discounts.all() if self.instance.pk else []
            self.fields["coupon_code_discounts"].initial = initial_discounts
            self.fields["coupon_code_discounts"].widget.choices = [
                (discount.pk, force_text(discount)) for discount in initial_discounts
            ]

    def save(self, commit=True):
        instance = super(CouponCodeForm, self).save(commit)
        instance.shops.set([self.shop])

        if "coupon_code_discounts" in self.fields:
            data = self.cleaned_data
            coupon_code_discount_ids = data.get("coupon_code_discounts", [])
            instance.coupon_code_discounts.set(
                Discount.objects.filter(shops=self.shop, id__in=coupon_code_discount_ids)
            )

        return instance


class CouponCodeEditView(CreateOrUpdateView):
    model = CouponCode
    form_class = CouponCodeForm
    template_name = "shuup/discounts/edit.jinja"
    context_object_name = "discounts"

    def get_queryset(self):
        return CouponCode.objects.filter(shops=get_shop(self.request))

    def get_toolbar(self):
        object = self.get_object()
        delete_url = (
            reverse_lazy("shuup_admin:discounts_coupon_codes.delete", kwargs={"pk": object.pk}) if object.pk else None
        )
        return get_default_edit_toolbar(self, self.get_save_form_id(), delete_url=delete_url)

    def get_form_kwargs(self):
        kwargs = super(CouponCodeEditView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class CouponCodeDeleteView(DetailView):
    model = CouponCode

    def get_queryset(self):
        return CouponCode.objects.filter(shops=get_shop(self.request))

    def post(self, request, *args, **kwargs):
        coupon = self.get_object()
        coupon.delete()
        messages.success(request, _("%s has been deleted.") % coupon)
        return HttpResponseRedirect(reverse_lazy("shuup_admin:discounts_coupon_codes.list"))
