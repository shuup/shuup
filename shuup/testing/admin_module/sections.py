# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from shuup.admin.base import Section


class MockContactSection(Section):
    identifier = "contact_mock_section"
    name = _("mock section title")
    icon = "fa-globe"
    template = "shuup_testing/_contact_mock_section.jinja"
    order = 9

    @staticmethod
    def visible_for_object(contact):
        return True

    @staticmethod
    def get_context_data(contact):
        context = {}
        context['mock_context'] = "mock section context data"
        return context
