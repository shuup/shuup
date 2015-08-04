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

        self.append(DropdownActionButton(
            menu_items,
            icon="fa fa-star",
            text=_(u"Actions"),
            extra_css_class="btn-info",
        ))
        # TODO: Add extensibility
