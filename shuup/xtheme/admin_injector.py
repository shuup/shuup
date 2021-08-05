# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import logging
from django.template import loader
from typing import TYPE_CHECKING, Optional

from shuup.admin.base import AdminTemplateInjector
from shuup.core.models import Shop, Supplier
from shuup.xtheme.models import AdminThemeSettings

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover
    from django.contrib.auth import get_user_model

    User = get_user_model()


class XthemeAdminTemplateInjector(AdminTemplateInjector):
    @classmethod
    def get_admin_template_snippet(cls, place: str, shop: "Shop", user: "User", supplier: "Optional[Supplier]"):
        if place == "head_end":
            admin_theme = AdminThemeSettings.objects.filter(shop=shop).first()
            if admin_theme and admin_theme.active:
                try:
                    return loader.render_to_string(
                        "shuup/xtheme/admin/admin_theme_injection.jinja",
                        context={
                            "admin_theme": admin_theme,
                        },
                    )
                except Exception:
                    LOGGER.exception("Failed to render snippet.")
