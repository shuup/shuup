# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from bootstrap3.renderers import FormRenderer
from django.utils.safestring import mark_safe
from django_jinja import library

from shoop.admin.template_helpers import shoop_admin as shoop_admin_template_helpers
from shoop.admin.utils.bs3_renderers import AdminFieldRenderer


class Bootstrap3Namespace(object):
    def field(self, field, **kwargs):
        if not field:
            return ""
        return mark_safe(AdminFieldRenderer(field, **kwargs).render())

    def form(self, form, **kwargs):
        return mark_safe(FormRenderer(form, **kwargs).render())

    def datetime_field(self, field, **kwargs):
        kwargs.setdefault("widget_class", "datetime")
        kwargs.setdefault("addon_after", "<span class='fa fa-calendar'></span>")
        return self.field(field, **kwargs)


library.global_function(name="shoop_admin", fn=shoop_admin_template_helpers)
library.global_function(name="bs3", fn=Bootstrap3Namespace())
