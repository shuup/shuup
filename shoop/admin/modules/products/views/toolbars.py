# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from shoop.admin.toolbar import (
    Toolbar, get_default_edit_toolbar,
    DropdownActionButton, DropdownItem, DropdownDivider
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

        media_button = DropdownItem(
            text=_("Manage Media"),
            icon="fa fa-picture-o",
            url=reverse("shoop_admin:product.edit_media", kwargs={"pk": product.pk}),
        )
        cross_sell_button = DropdownItem(
            text=_("Manage Cross-Selling"),
            icon="fa fa-exchange",
            url=reverse("shoop_admin:product.edit_cross_sell", kwargs={"pk": product.pk}),
        )
        menu_items = [
            media_button,
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
            yield DropdownItem(
                text=_("Manage Variations"),
                icon="fa fa-arrows-alt",
                url=variation_url,
            )
            for child in product.variation_children.all():
                yield DropdownItem(
                    text=_("Child: %s") % child,
                    icon="fa fa-long-arrow-down",
                    url=get_model_url(child),
                )
        elif variation_child:
            yield DropdownDivider()
            parent = product.variation_parent
            yield DropdownItem(
                text=_("Manage Variations"),
                icon="fa fa-arrows-alt",
                url=variation_url,
            )
            yield DropdownItem(
                text=_("Parent: %s") % parent,
                icon="fa fa-long-arrow-up",
                url=get_model_url(parent),
            )
            for sib in product.get_variation_siblings():
                yield DropdownItem(
                    text=_("Sibling: %s") % sib,
                    icon="fa fa-long-arrow-right",
                    url=get_model_url(sib),
                )
        elif package_parent:
            yield DropdownDivider()
            yield DropdownItem(
                text=_("Manage Package"),
                icon="fa fa-archive",
                url="#",  # TODO: Implement manage packages
            )
            for child in product.get_all_package_children():
                yield DropdownItem(
                    text=_("Child: %s") % child,
                    icon="fa fa-long-arrow-down",
                    url=get_model_url(child),
                )

        package_parents = list(product.get_all_package_parents())
        if package_parents:
            yield DropdownDivider()
            for parent in package_parents:
                yield DropdownItem(
                    text=_("Package Parent: %s") % parent,
                    icon="fa fa-long-arrow-up",
                    url=get_model_url(parent),
                )

        if not (variation_parent or variation_child or package_parent):
            yield DropdownDivider()
            yield DropdownItem(
                text=_("Convert to Variation Parent"),
                icon="fa fa-arrows-alt",
                url=variation_url,
            )
