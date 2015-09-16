# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.http import HttpResponse
from django.template.loader import render_to_string


def products(request):
    return HttpResponse(
        render_to_string(
            "classic_gray/products_view.jinja",
            request=request,
        )
    )
