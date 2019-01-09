# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import include, url
from rest_framework import routers
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token

from shuup.api.encoders import apply_monkeypatch
from shuup.apps.provides import get_provide_objects

from .docs import SwaggerSchemaView


class AutoRouter(routers.DefaultRouter):
    def populate(self):
        for func in get_provide_objects("api_populator"):
            func(router=self)

    def register(self, prefix, viewset, base_name=None):
        if base_name is None:
            base_name = prefix.replace('/', '-')
        super(AutoRouter, self).register(prefix, viewset, base_name)


apply_monkeypatch()
router = AutoRouter()
router.populate()

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^auth', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api-token-auth/', obtain_jwt_token),
    url(r'^api-token-refresh/', refresh_jwt_token),
    url(r'^docs/$', SwaggerSchemaView.as_view(), name="rest-docs")
]
