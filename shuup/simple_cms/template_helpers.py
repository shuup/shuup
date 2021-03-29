# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from jinja2.utils import contextfunction

from shuup.simple_cms.models import Page


class SimpleCMSTemplateHelpers(object):
    name = "simple_cms"

    @contextfunction
    def get_page_by_identifier(self, context, identifier):
        return Page.objects.for_shop(context["request"].shop).filter(identifier=identifier, deleted=False).first()

    @contextfunction
    def get_visible_pages(self, context):
        return Page.objects.visible(context["request"].shop, user=context["request"].user)
