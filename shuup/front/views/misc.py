# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.http import HttpResponseRedirect

from shuup import configuration


def toggle_all_seeing(request):
    return_url = request.META["HTTP_REFERER"]
    if not request.user.is_superuser:
        return HttpResponseRedirect(return_url)
    all_seeing_key = "is_all_seeing:%d" % request.user.pk
    is_all_seeing = not configuration.get(None, all_seeing_key, False)
    configuration.set(None, all_seeing_key, is_all_seeing)
    return HttpResponseRedirect(return_url)
