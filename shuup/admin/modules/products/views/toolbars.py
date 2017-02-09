# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from shuup.admin.toolbar import (
    DropdownActionButton, DropdownDivider, DropdownHeader, DropdownItem,
    get_default_edit_toolbar, JavaScriptActionButton, Toolbar
)
from shuup.admin.utils.urls import get_model_url
from shuup.apps.provides import get_provide_objects


class EditProductToolbar(Toolbar):
    def __init__(self, view):
        super(EditProductToolbar, self).__init__()
        self.view = view
        self.request = view.request
        self.product = view.object
        self.extend(get_default_edit_toolbar(
            self.view, "product_form",
            delete_url="shuup_admin:shop_product.delete"
        ))
        if self.product.pk:
            self._build_existing_product()

    def _build_existing_product(self):
        product = self.product
        # :type product: shuup.core.models.Product

        save_as_copy_button = JavaScriptActionButton(
            onclick="saveAsACopy()",
            text=_("Save as a copy"),
            icon="fa fa-clone",
            required_permissions=("shuup.add_product", "shuup.view_product")
        )
        self.append(save_as_copy_button)

        cross_sell_button = DropdownItem(
            text=_("Manage Cross-Selling"),
            icon="fa fa-random",
            url=reverse("shuup_admin:shop_product.edit_cross_sell", kwargs={"pk": product.pk}),
            required_permissions=("shuup.change_productcrosssell")
        )
        menu_items = [
            DropdownHeader(text=_("Cross-Selling")),
            cross_sell_button
        ]

        for item in self._get_variation_and_package_menu_items(product):
            menu_items.append(item)

        for button in get_provide_objects("admin_product_toolbar_action_item"):
            if button.visible_for_object(product):
                menu_items.append(button(product))

        if menu_items:
            self.append(DropdownActionButton(
                menu_items,
                icon="fa fa-star",
                text=_(u"Actions"),
                extra_css_class="btn-info"
            ))

    def _get_header_item(self, header):
        yield DropdownDivider()
        yield DropdownHeader(text=header)

    def _get_package_url(self, product):
        return reverse("shuup_admin:shop_product.edit_package", kwargs={"pk": product.pk})

    def _get_variation_url(self, product):
        return reverse("shuup_admin:shop_product.edit_variation", kwargs={"pk": product.pk})

    def _get_children_items(self, children):
        for child in children:
            yield DropdownItem(
                text=_("Child: %s") % child,
                icon="fa fa-eye",
                url=get_model_url(child),
            )

    def _get_parent_and_sibling_items(self, parent, siblings):
        yield DropdownItem(
            text=_("Parent: %s") % parent,
            icon="fa fa-eye",
            url=get_model_url(parent),
        )
        for sib in siblings:
            yield DropdownItem(
                text=_("Sibling: %s") % sib,
                icon="fa fa-eye",
                url=get_model_url(sib),
            )

    def _get_variation_menu_items(self, product):
        for item in self._get_header_item(_("Variations")):
            yield item
        yield DropdownItem(
            text=_("Manage Variations"),
            icon="fa fa-sitemap",
            url=self._get_variation_url(product),
            required_permissions=["shuup.change_product"]
        )
        if product.is_variation_parent():
            for child in self._get_children_items(product.variation_children.all()):
                yield child
        elif product.is_variation_child():
            for item in self._get_parent_and_sibling_items(product.variation_parent, product.get_variation_siblings()):
                yield item

    def _get_package_menu_items(self, product):
        for item in self._get_header_item(_("Packages")):
            yield item
        yield DropdownItem(
            text=_("Manage Package"),
            icon="fa fa-cube",
            url=self._get_package_url(product),
            required_permissions=["shuup.change_product"]
        )
        if product.is_package_parent():
            for child in self._get_children_items(product.get_all_package_children()):
                yield child
        elif product.is_package_child():
            for parent in product.get_all_package_parents():
                for item in self._get_parent_and_sibling_items(
                        parent, [sib for sib in parent.get_all_package_children() if sib != product]):
                    yield item

    def _get_variation_and_package_menu_items(self, product):
        is_variation_product = (product.is_variation_parent() or product.is_variation_child())
        if is_variation_product:
            for item in self._get_variation_menu_items(product):
                yield item

        is_package_product = (product.is_package_parent() or product.is_package_child())
        if is_package_product:
            for item in self._get_package_menu_items(product):
                yield item

        if not (is_variation_product or is_package_product):
            for item in self._get_header_item(_("Packages")):
                yield item
            yield DropdownItem(
                text=_("Convert to Package Parent"),
                icon="fa fa-retweet",
                url=self._get_package_url(product),
                required_permissions=["shuup.change_product"]
            )
            for item in self._get_header_item(_("Variations")):
                yield item
            yield DropdownItem(
                text=_("Convert to Variation Parent"),
                icon="fa fa-retweet",
                url=self._get_variation_url(product),
                required_permissions=["shuup.change_product"]
            )
