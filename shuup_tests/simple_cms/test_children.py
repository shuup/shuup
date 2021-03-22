# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
import pytest
from django.utils.encoding import force_text

from shuup.simple_cms.views import PageView
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import is_anonymous
from shuup_tests.simple_cms.utils import create_page


def check_children_content(request, page, children_content, children_visibility):
    view_func = PageView.as_view()
    response = view_func(request, url=page.url)
    response.render()

    assert page.get_html() in response.rendered_content
    assert bool(children_content in response.rendered_content) == children_visibility


@pytest.mark.django_db
def test_visible_children(rf):
    shop = get_default_shop()
    request = apply_request_middleware(rf.get("/"))
    assert is_anonymous(request.user)

    parent_content = "Parent content"
    page = create_page(available_from=datetime.date(1988, 1, 1), content=parent_content, shop=shop, url="test")
    children_content = "Children content"
    # Visible child
    create_page(available_from=datetime.date(2000, 1, 1), content=children_content, parent=page, shop=shop)

    assert page.list_children_on_page == False
    check_children_content(request, page, children_content, False)

    page.list_children_on_page = True
    page.save()
    check_children_content(request, page, children_content, True)

    # check timestamps
    page.show_child_timestamps = True
    page.save()
    page.refresh_from_db()

    view = PageView.as_view()
    response = view(request=request, pk=page.pk, url="test")
    response.render()
    content = force_text(response.content)
    assert "Children content" in content
    assert "Jan 1, 2000, 12:00:00 AM" in content

    page.show_child_timestamps = False
    page.save()
    page.refresh_from_db()
    view = PageView.as_view()
    response = view(request=request, pk=page.pk, url="test")
    response.render()
    content = force_text(response.content)
    assert "Children content" in content
    assert "Jan 1, 2000, 12:00:00 AM" not in content


@pytest.mark.django_db
def test_invisible_children(rf):
    shop = get_default_shop()
    request = apply_request_middleware(rf.get("/"))

    parent_content = "Parent content"
    page = create_page(available_from=datetime.date(1988, 1, 1), content=parent_content, shop=shop)
    children_content = "Children content"
    create_page(content=children_content, parent=page, shop=shop, available_from=None)  # Create invisible children

    assert page.list_children_on_page == False
    check_children_content(request, page, children_content, False)

    page.list_children_on_page = True
    page.save()
    check_children_content(request, page, children_content, False)
