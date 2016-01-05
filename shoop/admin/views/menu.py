# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.views.generic import TemplateView


class MenuView(TemplateView):
    template_name = "shoop/admin/base/_main_menu.jinja"
