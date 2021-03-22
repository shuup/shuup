# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup
from django.utils.encoding import force_text

from shuup.admin.modules.contacts.views.detail import ContactDetailView
from shuup.admin.modules.contacts.views.edit import ContactEditView
from shuup.apps.provides import override_provides
from shuup.testing.factories import create_random_person, get_default_shop
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_contact_edit_has_custom_toolbar_button(rf, admin_user):
    get_default_shop()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = ContactEditView.as_view()
    response = view_func(request, pk=contact.pk)
    content = force_text(response.render().content)
    assert "#mocktoolbarbutton" in content, "custom toolbar button not found on edit page"


@pytest.mark.django_db
def test_contact_detail_has_custom_toolbar_button(rf, admin_user):
    get_default_shop()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = ContactDetailView.as_view()
    response = view_func(request, pk=contact.pk)
    content = force_text(response.render().content)
    assert "#mocktoolbarbutton" in content, "custom toolbar button not found on detail page"


@pytest.mark.django_db
def test_contact_detail_has_custom_section(rf, admin_user):
    get_default_shop()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = ContactDetailView.as_view()
    response = view_func(request, pk=contact.pk)
    content = force_text(response.render().content)

    assert "mock section title" in content, "custom section title not found on detail page"
    assert "mock section content" in content, "custom section content not found on detail page"
    assert "mock section context data" in content, "custom section context data not found on detail page"


@pytest.mark.django_db
def test_contact_detail_has_mocked_toolbar_action_items(rf, admin_user):
    get_default_shop()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = ContactDetailView.as_view()
    with override_provides(
        "admin_contact_toolbar_action_item", ["shuup.testing.modules.mocker.toolbar:MockContactToolbarActionItem"]
    ):
        assert _check_if_mock_action_item_exists(view_func, request, contact)

    with override_provides("admin_contact_toolbar_action_item", []):
        assert not _check_if_mock_action_item_exists(view_func, request, contact)


def _check_if_mock_action_item_exists(view_func, request, contact):
    response = view_func(request, pk=contact.pk)
    soup = BeautifulSoup(response.render().content)
    for dropdown_link in soup.find_all("a", {"class": "dropdown-item"}):
        if dropdown_link.get("href", "") == "/#mocktoolbaractionitem":
            return True
    return False
