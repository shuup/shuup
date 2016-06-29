# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import activate

from shoop.core.models import OrderStatus, OrderStatusRole
from shoop_workbench.settings.base_settings import LANGUAGES


def create_default_order_statuses():
    for i, props in enumerate([
        {"name": _(u"received"), "role": OrderStatusRole.INITIAL, "identifier": "recv", "default": True},
        {"name": _(u"in progress"), "identifier": "prog"},
        {"name": _(u"complete"), "role": OrderStatusRole.COMPLETE, "identifier": "comp", "default": True},
        {"name": _(u"canceled"), "role": OrderStatusRole.CANCELED, "identifier": "canc", "default": True}
    ]):
        if not OrderStatus.objects.filter(identifier=props["identifier"]).exists():
            status_obj = OrderStatus.objects.create(ordering=i, **props)

            for lang_code, lang_name in LANGUAGES:
                activate(lang_code)
                status_obj.set_current_language(lang_code)
                status_obj.name = props["name"]
                status_obj.save()
