# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from .views import ProductFilterView

urlpatterns = [
    url(r'^categories/$',
        csrf_exempt(ProductFilterView.as_view()),
        name='categories_filter'),
]
