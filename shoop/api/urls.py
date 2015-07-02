# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import include, url
from rest_framework import routers
from shoop.api.encoders import apply_monkeypatch
from shoop.apps.provides import get_provide_objects


class AutoRouter(routers.DefaultRouter):
    def populate(self):
        for func in get_provide_objects("api_populator"):
            func(router=self)


apply_monkeypatch()
router = AutoRouter()
router.populate()

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^auth', include('rest_framework.urls', namespace='rest_framework'))
]
