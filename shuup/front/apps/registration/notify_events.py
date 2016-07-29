# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.dispatch import receiver
from registration.signals import user_registered

from shuup.notify import Event, Variable
from shuup.notify.typology import Email


class RegistrationReceived(Event):
    identifier = "registration_received"

    customer_email = Variable("Customer Email", type=Email)


@receiver(user_registered)
def send_user_registered_notification(user, **kwargs):
    RegistrationReceived(
        customer_email=user.email,
    ).run()
