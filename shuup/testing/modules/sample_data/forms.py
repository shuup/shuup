# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup.testing.modules.sample_data import manager as sample_manager
from shuup.testing.modules.sample_data.data import BUSINESS_SEGMENTS


class SampleObjectsWizardForm(forms.Form):
    BUSINESS_SEGMENT_CHOICES = sorted([(k, v["name"]) for k, v in BUSINESS_SEGMENTS.items()])

    business_segment = forms.ChoiceField(label=_("Business Segment"),
                                         required=True,
                                         choices=BUSINESS_SEGMENT_CHOICES,
                                         initial="default",
                                         help_text=_("Select your business segment "
                                                     "to install categories."))

    categories = forms.BooleanField(label=_("Install Categories"),
                                    initial=False,
                                    required=False,
                                    help_text=_("Check this to install sample categories."))

    products = forms.BooleanField(label=_("Install Products"),
                                  initial=False,
                                  required=False,
                                  help_text=_("Check this to install sample products."))

    def __init__(self, **kwargs):
        shop = kwargs.pop("shop")
        super(SampleObjectsWizardForm, self).__init__(**kwargs)

        if sample_manager.get_installed_categories(shop):
            self.fields["categories"].initial = True
            self.fields["categories"].widget = forms.CheckboxInput(attrs={'disabled': True})

        if sample_manager.get_installed_products(shop):
            self.fields["products"].initial = True
            self.fields["products"].widget = forms.CheckboxInput(attrs={'disabled': True})

        # no really choices to make - change to a hidden field widget
        if len(BUSINESS_SEGMENTS) == 1:
            self.fields["business_segment"].widget = forms.HiddenInput()

        # installed data means only one choice - the current installed one
        installed_bs = sample_manager.get_installed_business_segment(shop)
        if installed_bs:
            self.fields["business_segment"].initial = installed_bs
            self.fields["business_segment"].choices = [(installed_bs, BUSINESS_SEGMENTS[installed_bs]["name"])]

        # add the carousel option if its module is installed
        if 'shuup.front.apps.carousel' in settings.INSTALLED_APPS:
            has_installed_carousel = (sample_manager.get_installed_carousel(shop) is not None)
            self.fields["carousel"] = forms.BooleanField(
                label=_("Install Carousel"),
                initial=has_installed_carousel,
                required=False,
                widget=forms.CheckboxInput(attrs={"disabled": has_installed_carousel}),
                help_text=_("Check this to install a sample carousel.")
            )


class ConsolidateObjectsForm(forms.Form):

    def __init__(self, **kwargs):
        shop = kwargs.pop("shop")
        super(ConsolidateObjectsForm, self).__init__(**kwargs)

        if sample_manager.get_installed_categories(shop):
            self.fields["categories"] = forms.BooleanField(label=_("Uninstall Categories"),
                                                           initial=False,
                                                           required=False)

        if sample_manager.get_installed_products(shop):
            self.fields["products"] = forms.BooleanField(label=_("Uninstall Products"),
                                                         initial=False,
                                                         required=False)

        if sample_manager.get_installed_carousel(shop):
            self.fields["carousel"] = forms.BooleanField(
                label=_("Uninstall Carousel"),
                initial=False,
                required=False
            )
