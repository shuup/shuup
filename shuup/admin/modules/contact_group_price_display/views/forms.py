# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.forms import HiddenInput
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum

from shuup.admin.shop_provider import get_shop
from shuup.core.models import ContactGroupPriceDisplay, Shop, get_groups_for_price_display_create


class PriceDisplayChoices(Enum):
    NONE = "none"
    WITH_TAXES = "with_taxes"
    WITHOUT_TAXES = "without_taxes"
    HIDE = "hide"

    class Labels:
        NONE = _("unspecified")
        WITH_TAXES = _("show prices with taxes included")
        WITHOUT_TAXES = _("show pre-tax prices")
        HIDE = _("hide prices")


class ContactGroupPriceDisplayForm(forms.ModelForm):
    class Meta:
        model = ContactGroupPriceDisplay
        fields = (
            "group",
            "shop",
        )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(ContactGroupPriceDisplayForm, self).__init__(*args, **kwargs)
        shop = get_shop(self.request)
        if self.instance.pk:
            self.fields["group"].choices = [(self.instance.group.id, self.instance.group.name)]
            self.fields["group"].initial = self.instance.group
        else:
            self.fields["group"].choices = [
                (group.id, group.name) for group in get_groups_for_price_display_create(shop)
            ]

        self.fields["shop"] = forms.ModelChoiceField(
            queryset=Shop.objects.filter(pk=shop.id),
            initial=shop,
            widget=HiddenInput(),
            label=_("shop"),
            required=False,
        )

        self.fields["price_display_mode"] = forms.ChoiceField(
            choices=PriceDisplayChoices.choices(),
            label=_("Price display mode"),
            initial=get_price_display_mode(self.request, self.instance),
            help_text=_("Set how prices are displayed to contacts in this group."),
        )

    def clean_shop(self):
        return get_shop(self.request)

    def save(self, commit=True):
        price_display_mode = self.cleaned_data["price_display_mode"]
        super(ContactGroupPriceDisplayForm, self).save(commit=commit)
        _set_price_display_mode(self.request, self.instance.group, price_display_mode)


def get_price_display_mode(request, contact_group_price_display):
    shop = get_shop(request)
    if not contact_group_price_display.pk:
        return PriceDisplayChoices.NONE.value

    contact_group = contact_group_price_display.group
    if not contact_group.pk:
        return PriceDisplayChoices.NONE.value
    if contact_group.shop:
        assert contact_group.shop == shop
    price_display = contact_group.price_display_options.for_group_and_shop(contact_group, shop)
    taxes = price_display.show_prices_including_taxes
    hide = price_display.hide_prices
    if hide is None and taxes is None:
        return PriceDisplayChoices.NONE.value
    elif hide:
        return PriceDisplayChoices.HIDE.value
    elif taxes:
        return PriceDisplayChoices.WITH_TAXES.value
    else:
        return PriceDisplayChoices.WITHOUT_TAXES.value


def _set_price_display_mode(request, contact_group, price_display_mode):
    shop = get_shop(request)
    options = {}
    if contact_group.shop:
        assert contact_group.shop == shop

    if price_display_mode == PriceDisplayChoices.HIDE.value:
        options = {"hide_prices": True}
    elif price_display_mode == PriceDisplayChoices.WITH_TAXES.value:
        options = {
            "show_prices_including_taxes": True,
        }
    elif price_display_mode == PriceDisplayChoices.WITHOUT_TAXES.value:
        options = {
            "show_prices_including_taxes": False,
        }
    if options or price_display_mode == PriceDisplayChoices.NONE.value:
        options.update(dict(shop=shop))
        contact_group.set_price_display_options(**options)
