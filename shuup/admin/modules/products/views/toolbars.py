# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext as _
from enumfields import Enum

from shuup.admin.toolbar import (
    DropdownActionButton, DropdownDivider, DropdownHeader, DropdownItem,
    get_default_edit_toolbar, Toolbar
)
from shuup.admin.utils.urls import get_model_url
from shuup.apps.provides import get_provide_objects
from shuup.utils.django_compat import reverse


class ProductActionCategory(Enum):
    MAIN = 1
    CHILD_CROSS_SELL = 2
    CHILD_PACKAGE = 3
    CHILD_OTHER = 5


# TODO: Rewrite this for 2.0.
class EditProductToolbar(Toolbar):
    def __init__(self, view):
        super(EditProductToolbar, self).__init__()
        self.view = view
        self.request = view.request
        self.product = view.object.product
        self.extend(get_default_edit_toolbar(
            self.view, "product_form",
            delete_url="shuup_admin:shop_product.delete",
            with_save_as_copy=True,
            copy_url="shuup_admin:shop_product.copy"
        ))
        if self.product.pk:
            self._build_existing_product()

    def _build_existing_product(self):
        product = self.product
        # :type product: shuup.core.models.Product

        # static buttons
        self._build_action_menu(product)

    def _build_action_menu(self, product):
        # cross selling
        cross_sell_button = DropdownItem(
            text=_("Manage Cross-Selling"),
            icon="fa fa-random",
            url=reverse("shuup_admin:shop_product.edit_cross_sell", kwargs={"pk": product.pk})
        )
        menu_items = [menu_item for menu_item in self._get_header_items(
                header=_("Cross-Selling"), divider=False, identifier=ProductActionCategory.CHILD_CROSS_SELL)]
        menu_items.append(cross_sell_button)

        # packages
        for item in self._get_variation_and_package_menu_items(product):
            menu_items.append(item)

        provided_items = get_provide_objects("admin_product_toolbar_action_item")
        if provided_items:
            for item in self._get_header_items(header=_("Other"), identifier=ProductActionCategory.CHILD_OTHER):
                menu_items.append(item)

            for button in provided_items:
                if button.visible_for_object(product):
                    menu_items.append(button(product))

        # add the actual Action button
        self.append(DropdownActionButton(
            menu_items,
            icon="fa fa-star",
            text=_(u"Actions"),
            extra_css_class="btn-inverse btn-actions",
            identifier=ProductActionCategory.MAIN
        ))

    def _get_header_items(self, header, divider=True, identifier=None):
        if divider:
            yield DropdownDivider()
        yield DropdownHeader(text=header, identifier=identifier)

    def _get_package_url(self, product):
        return reverse("shuup_admin:shop_product.edit_package", kwargs={"pk": product.pk})

    def _get_children_items(self, children):
        for child in children:
            yield DropdownItem(
                text=_("Child: %s") % child,
                icon="fa fa-eye",
                url=get_model_url(child, shop=self.request.shop),
            )

    def _get_parent_and_sibling_items(self, parent, siblings):
        yield DropdownItem(
            text=_("Parent: %s") % parent,
            icon="fa fa-eye",
            url=get_model_url(parent, shop=self.request.shop),
        )
        for sib in siblings:
            yield DropdownItem(
                text=_("Sibling: %s") % sib,
                icon="fa fa-eye",
                url=get_model_url(sib, shop=self.request.shop),
            )

    def _get_package_menu_items(self, product):
        for item in self._get_header_items(_("Packages"), identifier=ProductActionCategory.CHILD_PACKAGE):
            yield item

        if product.is_package_parent():
            yield DropdownItem(
                text=_("Manage Package"),
                icon="fa fa-cube",
                url=self._get_package_url(product),
            )

            for child in self._get_children_items(product.get_all_package_children()):
                yield child
        elif product.is_package_child():
            for parent in product.get_all_package_parents():
                for item in self._get_parent_and_sibling_items(
                        parent, [sib for sib in parent.get_all_package_children() if sib != product]):
                    yield item

    def _get_variation_and_package_menu_items(self, product):
        is_package_product = (product.is_container() or product.is_package_child())
        if is_package_product:
            for item in self._get_package_menu_items(product):
                yield item

        if not is_package_product:
            # package header
            for item in self._get_header_items(_("Packages"), identifier=ProductActionCategory.CHILD_PACKAGE):
                yield item
            yield DropdownItem(
                text=_("Convert to Package Parent"),
                icon="fa fa-retweet",
                url=self._get_package_url(product),
            )
