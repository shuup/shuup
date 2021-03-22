# -- encoding: UTF-8 --
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import logging
from django.conf import settings

from .models import Script
from .script import Context

LOG = logging.getLogger(__name__)


def run_event(event, shop):
    """Run the event.
    :param shuup.notify.Event event: the event.
    :param shuup.Shop shop: the shop to run the event.
    """

    # TODO: Add possible asynchronous implementation.
    for script in Script.objects.filter(event_identifier=event.identifier, enabled=True, shop=shop):
        try:
            script.execute(context=Context.from_event(event, shop))
        except Exception:  # pragma: no cover
            if settings.DEBUG:
                raise
            LOG.exception("Error! Script %r failed for event %r." % (script, event))
