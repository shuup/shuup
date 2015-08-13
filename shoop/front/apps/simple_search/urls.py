# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import patterns, url

from .views import SearchView

urlpatterns = patterns(
    "",
    url(r"^search/$", SearchView.as_view(), name="product_search"),
)
