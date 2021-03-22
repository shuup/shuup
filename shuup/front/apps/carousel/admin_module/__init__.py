# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import CONTENT_MENU_CATEGORY
from shuup.admin.utils.urls import admin_url, derive_model_url, get_edit_and_list_urls
from shuup.front.apps.carousel.models import Carousel


class CarouselModule(AdminModule):
    name = _("Carousels")
    breadcrumbs_menu_entry = MenuEntry(text=name, url="shuup_admin:carousel.list", category=CONTENT_MENU_CATEGORY)

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^carousels",
            view_template="shuup.front.apps.carousel.admin_module.views.Carousel%sView",
            name_template="carousel.%s",
        ) + [
            admin_url(
                r"^carousel/(?P<pk>\d+)/delete/$",
                "shuup.front.apps.carousel.admin_module.views.CarouselDeleteView",
                name="carousel.delete",
            ),
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-image",
                url="shuup_admin:carousel.list",
                category=CONTENT_MENU_CATEGORY,
            )
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(Carousel, "shuup_admin:carousel", object, kind)
