# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import django.conf

from shuup.apps import AppConfig
from shuup.core.excs import MissingSettingException
from shuup.utils import money


class ShuupCoreAppConfig(AppConfig):
    name = "shuup.core"
    verbose_name = "Shuup Core"
    label = "shuup"  # Use "shuup" as app_label instead of "core"
    required_installed_apps = (
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "easy_thumbnails",
        "filer",
    )
    provides = {
        "api_populator": [
            "shuup.core.api:populate_core_api"
        ],
        "pricing_module": [
            "shuup.core.pricing.default_pricing:DefaultPricingModule"
        ],
    }

    def ready(self):
        from django.conf import settings
        if not getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE", None):
            raise MissingSettingException("PARLER_DEFAULT_LANGUAGE_CODE must be set.")
        if not getattr(settings, "PARLER_LANGUAGES", None):
            raise MissingSettingException("PARLER_LANGUAGES must be set.")

        # set money precision provider function
        from .models import get_currency_precision
        money.set_precision_provider(get_currency_precision)

        if django.conf.settings.SHUUP_ERROR_PAGE_HANDLERS_SPEC:
            from .error_handling import install_error_handlers
            install_error_handlers()

        from shuup.core.utils.context_cache import (
            bump_product_signal_handler, bump_shop_product_signal_handler
        )
        from shuup.core.models import Product, ShopProduct
        from django.db.models.signals import m2m_changed
        m2m_changed.connect(
            bump_shop_product_signal_handler,
            sender=ShopProduct.categories.through,
            dispatch_uid="shop_product:clear_shop_product_cache"
        )
        from django.db.models.signals import post_save
        post_save.connect(
            bump_product_signal_handler,
            sender=Product,
            dispatch_uid="product:bump_product_cache"
        )
        post_save.connect(
            bump_shop_product_signal_handler,
            sender=ShopProduct,
            dispatch_uid="shop_product:bump_shop_product_cache"
        )

        # extends SQLite with necessary functions
        from django.db.backends.signals import connection_created
        from shuup.core.utils.db import extend_sqlite_functions
        connection_created.connect(extend_sqlite_functions)


default_app_config = "shuup.core.ShuupCoreAppConfig"
