# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import get_company_contact, get_person_contact
from shuup.front.views.misc import force_anonymous_contact, force_company_contact, force_person_contact
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_force_contact_views(rf):
    shop = factories.get_default_shop()
    user = factories.create_random_user(is_staff=True)
    shop.staff_members.add(user)
    person_contact = get_person_contact(user)
    request = apply_request_middleware(rf.get("/"), user=user)
    assert request.customer == person_contact

    # Force contact to anonymous contact
    _call_force_view(request, force_anonymous_contact)

    # Re-process middlewares so we check the force contact
    request = apply_request_middleware(rf.get("/"), user=user)
    assert request.customer.is_anonymous
    assert_all_good_with_random_user()

    # Force contact to person contact
    _call_force_view(request, force_person_contact)

    request = apply_request_middleware(rf.get("/"), user=user)
    assert request.customer == person_contact
    assert_all_good_with_random_user()

    # Force contact to company contact. This also ensures
    # company contact for staff user if does not exists.
    _call_force_view(request, force_company_contact)

    request = apply_request_middleware(rf.get("/"), user=user)
    assert get_company_contact(user) == request.customer
    assert person_contact in request.customer.members.all()
    assert request.person == person_contact
    assert_all_good_with_random_user()

    # Finally force back to person contact. Now without
    # forcing the request would have company contact
    # since company contact for shop staff was created
    # while forcing company.
    _call_force_view(request, force_person_contact)

    request = apply_request_middleware(rf.get("/"), user=user)
    assert request.customer == person_contact
    assert get_person_contact(user) == person_contact
    assert_all_good_with_random_user()


@pytest.mark.django_db
def test_force_views_only_for_staff(rf):
    shop = factories.get_default_shop()
    user = factories.create_random_user(is_staff=True)
    person_contact = get_person_contact(user)

    # Start forcing. There shouldn't be any changes to
    # request customer due calling the force functions since
    # those just do the redirect in case the current is user
    # is not shop staff.
    request = apply_request_middleware(rf.get("/"), user=user)
    assert request.customer == person_contact

    _call_force_view(request, force_anonymous_contact)

    request = apply_request_middleware(rf.get("/"), user=user)
    assert request.customer == person_contact

    _call_force_view(request, force_person_contact)

    request = apply_request_middleware(rf.get("/"), user=user)
    assert request.customer == person_contact

    _call_force_view(request, force_company_contact)

    request = apply_request_middleware(rf.get("/"), user=user)
    assert request.customer == person_contact

    assert get_company_contact(user) is None


def _call_force_view(request, view):
    request.META["HTTP_REFERER"] = "/"
    response = view(request)
    assert response.status_code == 302  # redirect


def assert_all_good_with_random_user():
    assert not get_person_contact(factories.create_random_user()).is_anonymous
