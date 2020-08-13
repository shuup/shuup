# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.dispatch import Signal

notification_email_before_send = Signal(providing_args=["action", "message", "context"])
notification_email_sent = Signal(providing_args=["message", "context"])
