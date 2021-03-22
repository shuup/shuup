# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
import pytest

from shuup.simple_cms.models import Page
from shuup.simple_cms.views import PageView
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup_tests.simple_cms.utils import create_page


@pytest.mark.django_db
@pytest.mark.parametrize("template_name", ["page.jinja", "page_sidebar.jinja"])
def test_superuser_can_see_invisible_page(rf, template_name):
    template_path = "shuup/simple_cms/" + template_name
    page = create_page(template_name=template_path, available_from=datetime.date(1988, 1, 1), shop=get_default_shop())
    view_func = PageView.as_view()
    request = apply_request_middleware(rf.get("/"))
    response = view_func(request, url=page.url)
    response.render()
    assert response.template_name[0] == template_path
