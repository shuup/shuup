# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
import pytest
from bs4 import BeautifulSoup

from shuup.notify.admin_module.views.email_template import EmailTemplateEditView
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_media_view_images(rf, admin_user):
    shop = factories.get_default_shop()

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    request.user = admin_user

    view_func = EmailTemplateEditView.as_view()
    response = view_func(request)
    if hasattr(response, "render"):
        response.render()

    assert response.status_code == 200
    soup = BeautifulSoup(response.content)
    assert soup.find("div", {"class": "code-editor-with-preview-container"})
