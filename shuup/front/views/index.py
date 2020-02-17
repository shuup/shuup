# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "shuup/front/index.jinja"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        # TODO: dispatch_hook("get_context_data", view=self, context=context)
        return context
