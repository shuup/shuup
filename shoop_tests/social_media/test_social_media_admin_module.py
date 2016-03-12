# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.admin.module_registry import replace_modules
from shoop.social_media.admin_module import SocialMediaAdminModule
from shoop.social_media.admin_module.views import SocialMediaLinkEditView
from shoop.social_media.models import SocialMediaLink, SocialMediaLinkType
from shoop.testing.factories import get_default_shop
from shoop.testing.utils import apply_request_middleware
from shoop_tests.admin.utils import admin_only_urls


def create_social_media_link(type, url):
    return SocialMediaLink.objects.create(type=type, url=url)


@pytest.mark.django_db
def test_social_media_link_edit_view(rf, admin_user):
    get_default_shop()
    url = "http://www.facebook.com"
    link = create_social_media_link(type=SocialMediaLinkType.FACEBOOK, url=url)
    request = apply_request_middleware(rf.get("/"), user=admin_user)

    with replace_modules([SocialMediaAdminModule]):
        with admin_only_urls():
            view_func = SocialMediaLinkEditView.as_view()
            response = view_func(request, pk=link.pk)
            assert (url in response.rendered_content)
            response = view_func(request, pk=None)  # "new mode"
            assert response.rendered_content  # something is rendered
