# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from shoop.admin.toolbar import (
    DropdownActionButton, DropdownDivider, DropdownHeader, DropdownItem,
    get_default_edit_toolbar, Toolbar
)
from shoop.admin.utils.urls import get_model_url


class EditProductToolbar(Toolbar):
    def __init__(self, view):
        super(EditProductToolbar, self).__init__()
        self.view = view
        self.request = view.request
        self.product = view.object
        self.extend(get_default_edit_toolbar(
            self.view, "product_form",
            delete_url="shoop_admin:product.delete"
        ))
        if self.product.pk:
            self._build_existing_product()

    def _build_existing_product(self):
        product = self.product
        # :type product: shoop.core.models.Product

        cross_sell_button = DropdownItem(
            text=_("Manage Cross-Selling"),
            icon="fa fa-random",
            url=reverse("shoop_admin:product.edit_cross_sell", kwargs={"pk": product.pk}),
        )
        menu_items = [
            DropdownHeader(text=_("Cross-Selling")),
            cross_sell_button
        ]

        for item in self._get_variation_and_package_menu_items(product):
            menu_items.append(item)

        self.append(DropdownActionButton(
            menu_items,
            icon="fa fa-star",
            text=_(u"Actions"),
            extra_css_class="btn-info",
        ))
        # TODO: Add extensibility

    def _get_variation_and_package_menu_items(self, product):
        variation_parent = product.is_variation_parent()
        variation_child = product.is_variation_child()
        package_parent = product.is_package_parent()
        variation_url = reverse("shoop_admin:product.edit_variation", kwargs={"pk": product.pk})
        if variation_parent:
            yield DropdownDivider()
            yield DropdownHeader(text=_("Variations"))
            yield DropdownItem(
                text=_("Manage Variations"),
                icon="fa fa-sitemap",
                url=variation_url,
            )
            for child in product.variation_children.all():
                yield DropdownItem(
                    text=_("Child: %s") % child,
                    icon="fa fa-eye",
                    url=get_model_url(child),
                )
        elif variation_child:
            yield DropdownDivider()
            yield DropdownHeader(text=_("Variations"))
            parent = product.variation_parent
            yield DropdownItem(
                text=_("Manage Variations"),
                icon="fa fa-sitemap",
                url=variation_url,
            )
            yield DropdownItem(
                text=_("Parent: %s") % parent,
                icon="fa fa-eye",
                url=get_model_url(parent),
            )
            for sib in product.get_variation_siblings():
                yield DropdownItem(
                    text=_("Sibling: %s") % sib,
                    icon="fa fa-eye",
                    url=get_model_url(sib),
                )
        elif package_parent:
            yield DropdownDivider()
            yield DropdownHeader(text=_("Variations"))
            yield DropdownItem(
                text=_("Manage Package"),
                icon="fa fa-cube",
                url="#",  # TODO: Implement manage packages
            )
            for child in product.get_all_package_children():
                yield DropdownItem(
                    text=_("Child: %s") % child,
                    icon="fa fa-eye",
                    url=get_model_url(child),
                )

        package_parents = list(product.get_all_package_parents())
        if package_parents:
            yield DropdownDivider()
            yield DropdownHeader(text=_("Variations"))
            for parent in package_parents:
                yield DropdownItem(
                    text=_("Package Parent: %s") % parent,
                    icon="fa fa-eye",
                    url=get_model_url(parent),
                )

        if not (variation_parent or variation_child or package_parent):
            yield DropdownDivider()
            yield DropdownHeader(text=_("Variations"))
            yield DropdownItem(
                text=_("Convert to Variation Parent"),
                icon="fa fa-retweet",
                url=variation_url,
            )
