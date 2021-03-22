# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup.notify.base import Event, Variable
from shuup.notify.typology import Email, Model, Text


class PasswordReset(Event):
    identifier = "shuup_notify_password_reset"
    name = _("Password Reset")
    description = _("This event is triggered when password reset is requested.")

    site_name = Variable(_("Site name"), type=Text)
    uid = Variable(_("User secret"), type=Text)
    user_to_recover = Variable(_("User to recover"), type=Model(settings.AUTH_USER_MODEL))
    token = Variable(_("Token"), type=Text)
    recovery_url = Variable(_("Recovery URL"), type=Text)

    # Attribut name so email sending works with generic template
    # See: https://github.com/shuup/shuup/blob/master/shuup/notify/script_template/generic.py#L89
    customer_email = Variable(_("To Email"), type=Email)
