# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.template import loader


class AdminNavigationProvider(object):
    template_name = None

    @classmethod
    def render(cls, request, context):
        if not cls.template_name:
            return ""
        ctx = {}
        for k, v in six.iteritems(context):
            ctx[k] = v
        return loader.render_to_string(template_name=cls.template_name, context=ctx, request=request)


class HomeNavigationProvider(AdminNavigationProvider):
    template_name = "shuup/admin/base/nav_items/home.jinja"


class SupportNavigationProvider(AdminNavigationProvider):
    template_name = "shuup/admin/base/nav_items/support_id.jinja"


class FrontNavigationProvider(AdminNavigationProvider):
    template_name = "shuup/admin/base/nav_items/front.jinja"
