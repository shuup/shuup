# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

import shoop.core.models
from shoop.admin.urls import login
from shoop.front.middleware import ShoopFrontMiddleware
from shoop.front.views.index import IndexView
from shoop.testing.factories import get_default_shop
from shoop.testing.utils import apply_request_middleware
from shoop_tests.utils.fixtures import regular_user

from .fixtures import get_request

__all__ = ("regular_user",)  # noqa

def get_unprocessed_request():
    request = get_request()
    for attrname in ['shop', 'person', 'customer', 'basket']:
        assert not hasattr(request, attrname)
    return request


def check_request_attribute_basics(request):
    assert isinstance(request.shop, shoop.core.models.Shop)
    assert isinstance(request.person, shoop.core.models.Contact)
    assert isinstance(request.customer, shoop.core.models.Contact)
    assert isinstance(request.basket, shoop.front.basket.objects.BaseBasket)


# TODO: Make these tests faster by faking the Shop and not using database


@pytest.mark.django_db
def test_with_anonymous_user():
    get_default_shop()  # Create a shop

    mw = ShoopFrontMiddleware()
    request = get_unprocessed_request()

    mw.process_request(request)

    check_request_attribute_basics(request)

    assert isinstance(request.person, shoop.core.models.AnonymousContact)
    assert isinstance(request.customer, shoop.core.models.AnonymousContact)
    assert request.person == request.customer


@pytest.mark.django_db
def test_with_logged_in_user(regular_user):
    get_default_shop()  # Create a shop

    mw = ShoopFrontMiddleware()
    request = get_unprocessed_request()
    request.user = regular_user

    mw.process_request(request)

    check_request_attribute_basics(request)

    assert isinstance(request.person, shoop.core.models.PersonContact)
    assert isinstance(request.customer, shoop.core.models.PersonContact)
    assert request.person == request.customer


@pytest.mark.django_db
def test_timezone_setting(regular_user):
    get_default_shop()  # Create a shop

    mw = ShoopFrontMiddleware()
    request = get_unprocessed_request()
    request.user = regular_user

    some_tz = ('US/Hawaii' if settings.TIME_ZONE == 'UTC' else 'UTC')

    person = shoop.core.models.get_person_contact(regular_user)
    person.timezone = some_tz
    person.save()

    assert timezone.get_current_timezone_name() != some_tz

    mw.process_request(request)

    assert timezone.get_current_timezone_name() == some_tz


@pytest.mark.django_db
def test_intra_request_user_changing(rf, regular_user):
    get_default_shop()  # Create a shop
    mw = ShoopFrontMiddleware()
    request = apply_request_middleware(rf.get("/"), user=regular_user)
    mw.process_request(request)
    assert request.person == shoop.core.models.get_person_contact(regular_user)
    logout(request)
    assert request.user == AnonymousUser()
    assert request.person == shoop.core.models.AnonymousContact()
    assert request.customer == shoop.core.models.AnonymousContact()


@pytest.mark.django_db
def test_maintenance_mode(rf, regular_user, admin_user):
    shop = get_default_shop()
    shop.maintenance_mode = True
    shop.save()

    mw = ShoopFrontMiddleware()

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
