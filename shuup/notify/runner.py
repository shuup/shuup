# -- encoding: UTF-8 --
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import logging

from django.conf import settings

from .models import Script
from .script import Context

LOG = logging.getLogger(__name__)


def run_event(event):
    # TODO: Add possible asynchronous implementation.
    for script in Script.objects.filter(event_identifier=event.identifier, enabled=True):
        try:
            script.execute(context=Context.from_event(event))
        except Exception:  # pragma: no cover
            if settings.DEBUG:
                raise
            LOG.exception("Script %r failed for event %r" % (script, event))
