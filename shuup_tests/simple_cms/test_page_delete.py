# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest

from shuup.simple_cms.admin_module.views import PageDeleteView, PageListView
from shuup.simple_cms.models import Page
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup_tests.simple_cms.utils import create_page


@pytest.mark.django_db
def test_page_delete(rf, admin_user):
    request = apply_request_middleware(rf.post("/"), user=admin_user)

    page = create_page(url="bacon", shop=get_default_shop())
    assert Page.objects.filter(pk=page.pk).not_deleted().exists() is True

    delete_view = PageDeleteView.as_view()
    response = delete_view(request, **{"pk": page.pk})
    assert response.status_code == 302
    assert response.url == reverse("shuup_admin:simple_cms.page.list")

    assert Page.objects.filter(pk=page.pk).not_deleted().exists() is False

    page_two = create_page(url="bacon", shop=get_default_shop())
    assert Page.objects.filter(pk=page_two.pk).exists()


@pytest.mark.django_db
def test_ensure_deleted_inlist(rf, admin_user):
    page = create_page(url="bacon", shop=get_default_shop())

    list_view = PageListView.as_view()
    request = apply_request_middleware(rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=admin_user)

    response = list_view(request)
    data = json.loads(response.content.decode("utf-8"))
    assert data["pagination"]["nItems"] == 1

    page.soft_delete()
    response = list_view(request)
    data = json.loads(response.content.decode("utf-8"))
    assert data["pagination"]["nItems"] == 0
