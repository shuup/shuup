# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup

from shuup import configuration
from shuup.core.models import get_person_contact
from shuup.front.views.index import IndexView
from shuup.testing.factories import get_all_seeing_key, get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils.fixtures import regular_user


def do_request_and_asserts(rf, contact, maintenance=False, expect_all_seeing=False, expect_toolbar=False):
    request = apply_request_middleware(rf.get("/"), user=contact.user, customer=contact)
    response = IndexView.as_view()(request)
    response.render()
    soup = BeautifulSoup(response.content)
    if expect_toolbar:
        toolbar = soup.find("nav", {"class": "navbar-admin-tools"})
        assert toolbar

    if expect_toolbar:
        assert request.shop.maintenance_mode == maintenance
        maintenance_class = "badge-warning" if maintenance else "badge-success"
        assert soup.find("span", {"class": maintenance_class})

    texts = []
    for elem in soup.find_all("a"):
        texts.append(elem.text.strip())

    if contact.user.is_superuser:
        text = "show only visible products and categories" if expect_all_seeing else "show all products and categories"
        assert_text_in_texts(texts, text, True)
    else:
        assert_text_in_texts(texts, "show only visible products and categories", False)
        assert_text_in_texts(texts, "show all products and categories", False)


@pytest.mark.django_db
def test_all_seeing_and_maintenance(rf, admin_user):
    shop = get_default_shop()
    admin_contact = get_person_contact(admin_user)
    do_request_and_asserts(rf, admin_contact, maintenance=False, expect_toolbar=True)

    assert not admin_contact.is_all_seeing
    configuration.set(None, get_all_seeing_key(admin_user), True)
    assert admin_contact.is_all_seeing

    assert admin_contact.user.is_superuser
    do_request_and_asserts(rf, admin_contact, maintenance=False, expect_all_seeing=True, expect_toolbar=True)
    configuration.set(None, get_all_seeing_key(admin_contact), False)

    # Test maintenance mode badge
    shop.maintenance_mode = True
    shop.save()
    do_request_and_asserts(rf, admin_contact, maintenance=True, expect_toolbar=True)


def test_regular_user_is_blind(rf, regular_user):
    shop = get_default_shop()
    contact = get_person_contact(regular_user)
    do_request_and_asserts(rf, contact, maintenance=False, expect_all_seeing=False, expect_toolbar=False)

    # user needs to be superuser to even get a glimpse
    assert not contact.is_all_seeing
    configuration.set(None, get_all_seeing_key(contact), True)
    assert not contact.is_all_seeing  # only superusers can be allseeing

    # Contact might be all-seeing in database but toolbar requires superuser
    do_request_and_asserts(rf, contact, maintenance=False, expect_all_seeing=False, expect_toolbar=False)


def assert_text_in_texts(texts, expected_text, expected_outcome):
    return any([text for text in texts if expected_text in text]) == expected_outcome
