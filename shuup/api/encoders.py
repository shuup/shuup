# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import logging
from enum import Enum

from rest_framework.renderers import JSONRenderer
from rest_framework.utils import encoders

LOG = logging.getLogger(__name__)


class ExtJSONEncoder(encoders.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super(ExtJSONEncoder, self).default(obj)


def apply_monkeypatch():
    if JSONRenderer.encoder_class is encoders.JSONEncoder:
        JSONRenderer.encoder_class = ExtJSONEncoder
        LOG.info("`JSONRenderer.encoder_class` patched.")
