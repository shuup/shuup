# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import django.core.serializers.json
from django.utils.encoding import force_text
from django.utils.functional import Promise


class ExtendedJSONEncoder(django.core.serializers.json.DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, Promise):
            return force_text(o)
        return super(ExtendedJSONEncoder, self).default(o)
