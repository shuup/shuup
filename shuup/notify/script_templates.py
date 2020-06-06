# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from shuup.notify.script_template.factory import \
    generic_send_email_script_template_factory

from .notify_events import PasswordReset

mark_safe_lazy = lazy(mark_safe, six.text_type)


PASSWORD_RESET_EMAIL_TEMPLATE = mark_safe_lazy(_("""
<p>Hi {{ user_to_recover.get_full_name() }},</p>

<p>In case you've forgotten, your username is {{ user_to_recover.username }}.</p>
<p>You're receiving this email because you requested a password reset for your user account at {{ site_name }}.</p>
<p>Please go to the following page and choose a new password:</p>
<br>
<a href="{{ recovery_url }}">{{ recovery_url }}</a>
"""))


PasswordResetTemplate = generic_send_email_script_template_factory(
    identifier="shuup_notify_password_reset",
    event=PasswordReset,
    name=_("Send Password Reset Link"),
    description=_("""
        Send an email to user when their account password reset is requested
    """),
    help_text=_("""
        This script will send an email to user once their account password reset is
        requested either by admin, staff or user.
    """),
    initial={
        "en-subject": "Password Recovery",
        "en-body": PASSWORD_RESET_EMAIL_TEMPLATE
    }
)
