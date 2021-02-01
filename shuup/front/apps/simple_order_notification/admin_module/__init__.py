# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.template import engines
from django.template.utils import InvalidTemplateEngineError
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, Notification


class SimpleOrderNotificationModule(AdminModule):
    name = _("Simple order notifications")
    category = name

    def get_notifications(self, request):
        try:
            engines["jinja2"]
        except InvalidTemplateEngineError:
            text = """Simple Order Notifications can't send order notifications
because it can't find a Jinja2 template engine. Name your Jinja2 template engine "jinja2" to resolve this."""
            yield Notification(text=text)

    def get_required_permissions(self):
        return ("Access order notification module",)
