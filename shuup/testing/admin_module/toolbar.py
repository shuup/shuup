# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.toolbar import URLActionButton


class MockContactToolbarButton(URLActionButton):
    def __init__(self, contact, **kwargs):

        kwargs["icon"] = "fa fa-user"
        kwargs["text"] = _("Hello") + contact.full_name
        kwargs["extra_css_class"] = "btn-info"
        kwargs["url"] = "/#mocktoolbarbutton"

        self.contact = contact

        super(MockContactToolbarButton, self).__init__(**kwargs)
