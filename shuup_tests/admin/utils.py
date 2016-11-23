# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup_tests.utils import replace_urls


def get_admin_only_urls():
    from django.conf.urls import patterns, url, include
    from shuup.admin.urls import get_urls
    class FauxUrlPatternsModule:
        urlpatterns = get_urls()

    return patterns('',
        url(r'^sa/', include(FauxUrlPatternsModule, namespace="shuup_admin", app_name="shuup_admin")),
    )

def admin_only_urls():
    return replace_urls(get_admin_only_urls())
