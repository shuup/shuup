# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from django.utils.encoding import force_text

from shuup.admin.modules.contacts.views.detail import ContactDetailView
from shuup.admin.modules.contacts.views.edit import ContactEditView
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
    assert "#mocktoolbarbutton" in content, 'custom toolbar button not found on edit page'


@pytest.mark.django_db
def test_contact_detail_has_custom_toolbar_button(rf, admin_user):
    get_default_shop()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = ContactDetailView.as_view()
    response = view_func(request, pk=contact.pk)
    content = force_text(response.render().content)
    assert "#mocktoolbarbutton" in content, 'custom toolbar button not found on detail page'


@pytest.mark.django_db
def test_contact_detail_has_custom_section(rf, admin_user):
    get_default_shop()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = ContactDetailView.as_view()
    response = view_func(request, pk=contact.pk)
    content = force_text(response.render().content)

    assert "mock section title" in content, 'custom section title not found on detail page'
    assert "mock section content" in content, 'custom section content not found on detail page'
    assert "mock section context data" in content, 'custom section context data not found on detail page'
    
