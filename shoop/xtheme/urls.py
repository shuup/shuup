# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import url
from shoop.xtheme.views.editor import EditorView

from .views import xtheme_dispatch

urlpatterns = [
    url(r"^xtheme/$", xtheme_dispatch, name="xtheme"),
    url(r"^xtheme/editor/$", EditorView.as_view(), name="xtheme_editor"),
]
