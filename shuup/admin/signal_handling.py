# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from shuup.admin.modules.orders.receivers import (
    handle_custom_payment_return_requests
)
from shuup.core import cache
from shuup.core.order_creator.signals import order_creator_finished


@receiver(m2m_changed, sender=get_user_model().groups.through)
def on_user_groups_change(instance, action, model, **kwargs):
    from shuup.admin.utils.permissions import USER_PERMISSIONS_CACHE_NAMESPACE
    # a group has changed it's users relation through group.users.set()
    # then we need to bump the entire cache
    if isinstance(instance, Group):
        cache.bump_version(USER_PERMISSIONS_CACHE_NAMESPACE)

    # bump only the user's permission cache
    elif isinstance(instance, get_user_model()):
        cache.bump_version("{}:{}".format(USER_PERMISSIONS_CACHE_NAMESPACE, instance.pk))


order_creator_finished.connect(
    handle_custom_payment_return_requests,
    dispatch_uid='shuup.admin.handle_cash_payments'
)
