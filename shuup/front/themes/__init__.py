# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.widgets import TextEditorWidget
from shuup.utils.djangoenv import has_installed


class BaseThemeFieldsMixin(object):
    """
    Default Theme mixing with fields used in Shuup Front

    Add this mixing to the theme class if you want to use the same options as
    the Shuup Front theme provides.
    """

    _base_fields = [
        ("hide_prices", forms.BooleanField(required=False, initial=False, label=_("Hide prices"))),
        ("catalog_mode", forms.BooleanField(required=False, initial=False, label=_("Set shop in catalog mode"))),
        (
            "show_supplier_info",
            forms.BooleanField(
                required=False,
                initial=False,
                label=_("Show supplier info"),
                help_text=_("Show supplier name in product-box, product-detail, basket- and order-lines"),
            ),
        ),
        (
            "show_product_detail_section",
            forms.BooleanField(
                required=False,
                initial=True,
                label=_("Show Product Details"),
                help_text=_("If you enable this, extra information will be shown on product page in frontend."),
            ),
        ),
        (
            "show_variation_buttons",
            forms.BooleanField(
                required=False,
                initial=False,
                label=_("Show Variations as Buttons"),
                help_text=_("If you enable this, the variations will be shown as buttons instead of dropdowns."),
            ),
        ),
        (
            "product_detail_extra_tab_title",
            forms.CharField(
                required=False,
                label=_("Product detail extra tab title"),
                help_text=_("Enter the title for the product detail extra tab."),
            ),
        ),
        (
            "product_detail_extra_tab_content",
            forms.CharField(
                widget=TextEditorWidget(),
                required=False,
                label=_("Product detail extra tab content"),
                help_text=_("Enter the content for the product detail extra tab."),
            ),
        ),
    ]

    def get_product_tabs_options(self):
        product_detail_tabs = [
            ("description", _("Description")),
            ("details", _("Details")),
            ("attributes", _("Attributes")),
            ("files", _("Files")),
        ]
        if has_installed("shuup_product_reviews"):
            product_detail_tabs.append(("product_reviews", _("Product reviews")))
        return product_detail_tabs

    def get_base_fields(self):
        fields = self._base_fields
        product_detail_tabs = self.get_product_tabs_options()
        fields.extend(
            [
                (
                    "product_detail_tabs",
                    forms.MultipleChoiceField(
                        required=False,
                        initial=[tab[0] for tab in product_detail_tabs],
                        choices=product_detail_tabs,
                        label=_("Product detail tabs"),
                        help_text=_("Select all tabs that should be rendered in product details."),
                    ),
                )
            ]
        )
        return fields

    def get_product_details_tabs(self):
        selected_options = self.get_setting("product_detail_tabs")
        tab_options = self.get_product_tabs_options()

        # nothing selected, returns everything by default
        if not selected_options:
            return tab_options

        tabs = []
        for selected_option in selected_options:
            for tab_option in tab_options:
                if selected_option == tab_option[0]:
                    tabs.append(tab_option)
        return tabs

    def should_render_product_detail_tab(self, tab_identifier):
        return tab_identifier in [tab[0] for tab in self.get_product_details_tabs()]
