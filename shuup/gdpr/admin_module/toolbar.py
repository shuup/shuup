# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from shuup.admin.toolbar import PostActionButton


class AnonymizeContactToolbarButton(PostActionButton):
    def __init__(self, object, **kwargs):
        kwargs["icon"] = "fa fa-user-times"
        kwargs["text"] = _("Anonymize")
        kwargs["extra_css_class"] = "dropdown-item"
        kwargs["confirm"] = _(
            "This action will replace all contact personal data with random values making it "
            "impossible to be identified. The account will also be deactivated and any "
            "pending order(s) will be canceled. Are you sure?"
        )
        kwargs["name"] = "download"
        kwargs["value"] = "1"
        kwargs["post_url"] = reverse("shuup_admin:gdpr.anonymize", kwargs=dict(pk=object.pk))
        super(AnonymizeContactToolbarButton, self).__init__(**kwargs)

    @staticmethod
    def visible_for_object(object):
        return True


class DownloadDataToolbarButton(PostActionButton):
    def __init__(self, object, **kwargs):
        kwargs["icon"] = "fa fa-cube"
        kwargs["text"] = _("Download data")
        kwargs["name"] = "download"
        kwargs["value"] = "1"
        kwargs["extra_css_class"] = "dropdown-item"
        kwargs["post_url"] = reverse("shuup_admin:gdpr.download_data", kwargs=dict(pk=object.pk))
        super(DownloadDataToolbarButton, self).__init__(**kwargs)

    @staticmethod
    def visible_for_object(object):
        return True
