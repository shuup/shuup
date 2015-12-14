# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import url

from shoop.xtheme.views.command import command_dispatch
from shoop.xtheme.views.editor import EditorView
from shoop.xtheme.views.extra import extra_view_dispatch

urlpatterns = [
    url(r"^xtheme/editor/$", EditorView.as_view(), name="xtheme_editor"),
    url(r"^xtheme/(?P<view>.+)/*$", extra_view_dispatch, name="xtheme_extra_view"),
    url(r"^xtheme/$", command_dispatch, name="xtheme"),
]
