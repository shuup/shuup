# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django_jinja import library


class GDPRNamespace(object):
    def is_enabled(self, request, **kwargs):
        from shuup.gdpr.models import GDPRSettings
        return GDPRSettings.get_for_shop(request.shop).enabled

    def get_documents(self, request, **kwargs):
        from shuup.simple_cms.models import Page, PageType
        return Page.objects.visible(shop=request.shop).filter(page_type=PageType.REVISIONED)


library.global_function(name="gdpr", fn=GDPRNamespace())
