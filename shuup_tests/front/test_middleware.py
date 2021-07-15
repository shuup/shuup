# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from importlib import import_module

import pytest
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings
from django.utils import timezone

import shuup.core.models
from shuup.admin.urls import login
from shuup.core.models import (
    AnonymousContact,
    CompanyContact,
    Contact,
    PersonContact,
    Shop,
    get_company_contact,
    get_person_contact,
)
from shuup.front.middleware import ShuupFrontMiddleware
from shuup.front.views.index import IndexView
from shuup.testing.factories import create_random_company, get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils.fixtures import regular_user

from .fixtures import get_request

__all__ = ("regular_user",)  # noqa


def get_unprocessed_request():
    request = get_request()
    for attrname in ["shop", "person", "customer", "basket"]:
        assert not hasattr(request, attrname)
    return request


def check_request_attribute_basics(request):
    assert isinstance(request.shop, Shop)
    assert isinstance(request.person, Contact)
    assert isinstance(request.customer, Contact)
    assert isinstance(request.basket, shuup.front.basket.objects.BaseBasket)


# TODO: Make these tests faster by faking the Shop and not using database


def apply_session_storage(request):
    engine = import_module(settings.SESSION_ENGINE)
    engine.SessionStore
    request.session = engine.SessionStore("sessionid")
    return request


@pytest.mark.django_db
def test_with_anonymous_user():
    get_default_shop()  # Create a shop

    mw = ShuupFrontMiddleware()
    request = apply_session_storage(get_unprocessed_request())

    mw.process_request(request)

    check_request_attribute_basics(request)

    assert isinstance(request.person, AnonymousContact)
    assert isinstance(request.customer, AnonymousContact)
    assert request.person == request.customer


@pytest.mark.django_db
def test_with_logged_in_user(regular_user):
    get_default_shop()  # Create a shop

    mw = ShuupFrontMiddleware()
    request = apply_session_storage(get_unprocessed_request())
    request.user = regular_user

    mw.process_request(request)

    check_request_attribute_basics(request)

    assert isinstance(request.person, PersonContact)
    assert isinstance(request.customer, PersonContact)
    assert request.person == request.customer


@pytest.mark.django_db
def test_customer_company_member(regular_user):
    get_default_shop()  # Create a shop

    mw = ShuupFrontMiddleware()
    request = apply_session_storage(get_unprocessed_request())
    request.user = regular_user
    person = get_person_contact(regular_user)
    company = create_random_company()
    company.members.add(person)

    assert get_company_contact(regular_user) == company

    mw.process_request(request)

    check_request_attribute_basics(request)

    assert isinstance(request.person, PersonContact)
    assert isinstance(request.customer, CompanyContact)

    company = get_company_contact(request.user)
    assert company and (company == request.customer)


@pytest.mark.django_db
def test_timezone_setting(regular_user, admin_user):
    get_default_shop()  # Create a shop

    mw = ShuupFrontMiddleware()
    request = apply_session_storage(get_unprocessed_request())
    second_request = apply_session_storage(get_unprocessed_request())
    request.user = regular_user
    second_request.user = admin_user
    user_tz = "US/Hawaii" if settings.TIME_ZONE != "US/Hawaii" else "Europe/Stockholm"
    original_tz = timezone.get_current_timezone_name()

    assert timezone.get_current_timezone_name() == settings.TIME_ZONE
    mw.process_request(request)

    assert timezone.get_current_timezone_name() == settings.TIME_ZONE
    assert request.TIME_ZONE == settings.TIME_ZONE

    # Test the users timezone
    person = get_person_contact(regular_user)
    person.timezone = user_tz
    person.save()

    mw.process_request(request)

    assert timezone.get_current_timezone_name() == user_tz
    assert request.TIME_ZONE == user_tz

    # Test that the settings.TIME_ZONE gets activated if there is nothing else to fallback on
    mw.process_request(second_request)

    assert timezone.get_current_timezone_name() == settings.TIME_ZONE
    assert second_request.TIME_ZONE == settings.TIME_ZONE

    timezone.activate(original_tz)


@pytest.mark.django_db
def test_intra_request_user_changing(rf, regular_user):
    get_default_shop()  # Create a shop
    mw = ShuupFrontMiddleware()
    request = apply_request_middleware(rf.get("/"), user=regular_user)
    mw.process_request(request)
    assert request.person == get_person_contact(regular_user)
    logout(request)
    assert request.user == AnonymousUser()
    assert request.person == AnonymousContact()
    assert request.customer == AnonymousContact()


@pytest.mark.django_db
def test_maintenance_mode(rf, regular_user, admin_user):
    shop = get_default_shop()
    shop.maintenance_mode = True
    shop.save()

    mw = ShuupFrontMiddleware()

    request = apply_request_middleware(rf.get("/"), user=regular_user)
    maintenance_response = mw.process_view(request, IndexView)
    assert maintenance_response is not None
    assert maintenance_response.status_code == 503
    assert mw._get_maintenance_response(request, IndexView).content == maintenance_response.content

    login_response = mw.process_view(request, login)
    assert login_response is None

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    admin_response = mw.process_view(request, IndexView)
    assert admin_response is None

    shop.maintenance_mode = False
    shop.save()


@pytest.mark.django_db
def test_with_inactive_contact(rf, regular_user, admin_user):
    get_default_shop()  # Create a shop
    # Get or create contact for regular user
    contact = get_person_contact(regular_user)
    assert contact.is_active
    contact.is_active = False
    contact.save()

    request = apply_request_middleware(rf.get("/"), user=regular_user)
    mw = ShuupFrontMiddleware()
    mw.process_request(request)

    assert request.user == AnonymousUser()
    assert request.person == AnonymousContact()
    assert request.customer == AnonymousContact()


@pytest.mark.django_db
def test_with_statics(rf):
    shop = get_default_shop()  # Create a shop

    request = apply_request_middleware(rf.get("/static/test.png"))
    assert hasattr(request, "customer")  # Since debug is False

    request = apply_request_middleware(rf.get("/"))
    assert hasattr(request, "customer")

    with override_settings(DEBUG=True):
        request = apply_request_middleware(rf.get("/static/test.png"))
        assert not hasattr(request, "customer")  # Since debug is True

        request = apply_request_middleware(rf.get("/"))
        assert hasattr(request, "customer")
