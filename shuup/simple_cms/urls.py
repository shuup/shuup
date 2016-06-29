# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import patterns, url

from shuup.simple_cms.views import PageView

urlpatterns = patterns(
    '',
    url(r'^(?P<url>.*)/$',
        PageView.as_view(),
        name='cms_page'),
)
