# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shoop.admin.utils.picotable import Column
from shoop.admin.utils.views import PicotableListView
from shoop.social_media.models import SocialMediaLink


class SocialMediaLinkListView(PicotableListView):
    model = SocialMediaLink
    columns = [
        Column(
            "ordering",
            _("Ordering"),
            sort_field="ordering",
            display="ordering",
        ),
        Column(
            "type",
            _("Type"),
            sort_field="type",
            display="type",
        ),
        Column(
            "url",
            _("URL"),
            sort_field="url",
            display="url",
        ),
    ]
