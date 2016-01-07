# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.exceptions import ObjectDoesNotExist

from shoop.simple_cms.models import Page


class SimpleCMSTemplateHelpers(object):
    name = "simple_cms"

    def get_page_by_identifier(self, identifier):
        try:
            return Page.objects.get(identifier=identifier)
        except ObjectDoesNotExist:
            return None

    def get_visible_pages(self):
        return Page.objects.visible()
