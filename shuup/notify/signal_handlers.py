# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.dispatch import receiver

from shuup.core.signals import user_reset_password_requested
from shuup.core.tasks import run_task
from shuup.notify.models import Script
from shuup.notify.notify_events import PasswordReset


@receiver(user_reset_password_requested)
def on_user_requested_reset_password(sender, shop, user, reset_domain_url, reset_url_name, **kwargs):
    if Script.objects.filter(enabled=True, event_identifier=PasswordReset.identifier).exists():
        run_task(
            "shuup.notify.tasks.send_user_reset_password_email",
            user_id=user.pk,
            shop_id=shop.pk,
            reset_domain_url=reset_domain_url,
            reset_url_name=reset_url_name,
        )
        # handled!
        return True
    return False
