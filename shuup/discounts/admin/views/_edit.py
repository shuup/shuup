# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import MenuEntry
from shuup.admin.forms.fields import PercentageField
from shuup.admin.forms.widgets import (
    ContactChoiceWidget, ProductChoiceWidget, QuickAddCategorySelect,
    QuickAddContactGroupSelect
)
from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Category, ContactGroup, Supplier
from shuup.discounts.admin.widgets import (
    QuickAddAvailabilityExceptionMultiSelect, QuickAddCouponCodeSelect,
    QuickAddHappyHourMultiSelect
)
from shuup.discounts.models import (
    AvailabilityException, CouponCode, Discount, HappyHour
)
from shuup.utils.django_compat import reverse_lazy


class DiscountForm(forms.ModelForm):
    discount_percentage = PercentageField(
        max_digits=6, decimal_places=5, required=False,
        label=_("Discount percentage"),
        help_text=_("The discount percentage for this discount."))

    class Meta:
        model = Discount
        exclude = ("shops", "created_by", "modified_by")
        widgets = {
            "category": QuickAddCategorySelect(editable_model="shuup.Category"),
            "contact_group": QuickAddContactGroupSelect(editable_model="shuup.ContactGroup"),
            "coupon_code": QuickAddCouponCodeSelect(editable_model="discounts.CouponCode"),
            "availability_exceptions": QuickAddAvailabilityExceptionMultiSelect(),
            "happy_hours": QuickAddHappyHourMultiSelect()
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.shop = get_shop(self.request)
        super(DiscountForm, self).__init__(*args, **kwargs)

        self.fields["availability_exceptions"].queryset = AvailabilityException.objects.filter(shops=self.shop)
        self.fields["category"].queryset = Category.objects.filter(shops=self.shop)
        self.fields["contact"].widget = ContactChoiceWidget(clearable=True)
        self.fields["contact_group"].queryset = ContactGroup.objects.filter(shop=self.shop)
        self.fields["coupon_code"].queryset = CouponCode.objects.filter(shops=self.shop)
        self.fields["happy_hours"].queryset = HappyHour.objects.filter(shops=self.shop)
        self.fields["product"].widget = ProductChoiceWidget(clearable=True)
        self.fields["supplier"].queryset = Supplier.objects.enabled().filter(shops=self.shop)

    def save(self, commit=True):
        instance = super(DiscountForm, self).save(commit)
        instance.shops.set([self.shop])
        return instance


class DiscountEditView(CreateOrUpdateView):
    model = Discount
    form_class = DiscountForm
    template_name = "shuup/discounts/discount_edit.jinja"
    context_object_name = "discounts"

    def get_queryset(self):
        return Discount.objects.filter(shops=get_shop(self.request))

    def get_form_kwargs(self):
        kwargs = super(DiscountEditView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_breadcrumb_parents(self):
        if not self.object.active:
            return [
                MenuEntry(
                    text=_("Archived Product Discounts"),
                    url="shuup_admin:discounts.archive"
                )
            ]

        return [
            MenuEntry(
                text=force_text(self.model._meta.verbose_name_plural).title(),
                url="shuup_admin:discounts.list"
            )
        ]

    def get_toolbar(self):
        object = self.get_object()
        delete_url = (
            reverse_lazy("shuup_admin:discounts.delete", kwargs={"pk": object.pk})
            if object.pk else None)
        return get_default_edit_toolbar(self, self.get_save_form_id(), delete_url=delete_url)
