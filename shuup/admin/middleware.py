# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.contrib.auth.signals import user_logged_out

from shuup.admin.shop_provider import set_shop, unset_shop


class ShuupAdminMiddleware(object):
    def process_request(self, request):
        set_shop(request)

    @classmethod
    def refresh_on_logout(cls, request, **kwargs):
        unset_shop(request)


if (
    "django.contrib.auth" in settings.INSTALLED_APPS and
    "shuup.admin.middleware.ShuupAdminMiddleware" in settings.MIDDLEWARE_CLASSES
):
    user_logged_out.connect(ShuupAdminMiddleware.refresh_on_logout, dispatch_uid="shuup_admin_refresh_on_logout")
