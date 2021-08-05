# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
import json
import pytest
from django.http.response import Http404
from django.test import override_settings

from shuup.admin.shop_provider import set_shop
from shuup.core.models import Shop
from shuup.discounts.admin.views import HappyHourDeleteView, HappyHourEditView, HappyHourListView
from shuup.discounts.models import Discount, HappyHour
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


def _assert_view_get(rf, instance, shop, user, raises_404=False):
    request = apply_request_middleware(rf.get("/"), user=user, shop=shop)
    set_shop(request, shop)
    view_func = HappyHourEditView.as_view()
    if raises_404:
        with pytest.raises(Http404):
            view_func(request, pk=instance.pk)
    else:
        response = view_func(request, pk=instance.pk)
        assert response.status_code == 200


@pytest.mark.django_db
def test_happy_hours_admin_edit_view(rf, staff_user, admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        shop = factories.get_default_shop()
        shop.staff_members.add(staff_user)
        factories.get_shop(identifier="shop2", enabled=True)
        assert Shop.objects.count() == 2

        # Staff user gets shop automatically
        data = {
            "name": "Happiest Hour 2pm",
            "weekdays": [6],  # Sun
            "from_hour": datetime.time(hour=14, minute=0),
            "to_hour": datetime.time(hour=14, minute=0),
        }
        request = apply_request_middleware(rf.post("/", data=data), user=staff_user, shop=shop)
        set_shop(request, shop)
        assert request.shop == shop
        view_func = HappyHourEditView.as_view()
        response = view_func(request)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == 302
        happy_hour1 = HappyHour.objects.first()
        assert happy_hour1 is not None
        assert happy_hour1.shop == shop
        assert happy_hour1.time_ranges.count() == 1  # Since happy hour starts and ends on same day

        # Test with superuser and with different shop
        shop2 = factories.get_shop(enabled=True)
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user, shop=shop2)
        set_shop(request, shop2)
        view_func = HappyHourEditView.as_view()
        response = view_func(request)
        assert response.status_code == 302
        assert HappyHour.objects.count() == 2

        happy_hour2 = HappyHour.objects.exclude(id=happy_hour1.pk).first()
        assert happy_hour1 != happy_hour2
        assert happy_hour2.shop == shop2

        # Staff user can only view coupon codes since that has the right shop
        _assert_view_get(rf, happy_hour1, shop, staff_user)
        _assert_view_get(rf, happy_hour2, shop, staff_user, True)

        # Superuser can see both if needed, but only when right shop is active
        _assert_view_get(rf, happy_hour1, shop, admin_user)
        _assert_view_get(rf, happy_hour2, shop, admin_user, True)
        _assert_view_get(rf, happy_hour2, shop2, admin_user)


@pytest.mark.django_db
def test_happy_hours_admin_edit_view_over_midnight(rf, staff_user, admin_user):
    shop = factories.get_default_shop()
    shop.staff_members.add(staff_user)
    factories.get_shop(identifier="shop2", enabled=True)
    assert Shop.objects.count() == 2

    # Staff user gets shop automatically
    from_hour = datetime.time(hour=21, minute=0)
    to_hour = datetime.time(hour=3, minute=0)
    data = {"name": "Happiest Hour 2pm", "weekdays": [1], "from_hour": from_hour, "to_hour": to_hour}  # Tue
    request = apply_request_middleware(rf.post("/", data=data), user=staff_user, shop=shop)
    set_shop(request, shop)
    assert request.shop == shop
    view_func = HappyHourEditView.as_view()
    response = view_func(request)
    if hasattr(response, "render"):
        response.render()

    assert response.status_code == 302

    happy_hour = HappyHour.objects.first()
    assert happy_hour is not None
    assert happy_hour.shop == shop
    assert happy_hour.time_ranges.count() == 2  # Since happy hour starts and ends on different day
    assert happy_hour.time_ranges.filter(weekday=1).exists()
    assert happy_hour.time_ranges.filter(weekday=1, from_hour=from_hour, to_hour=datetime.time(23, 59)).exists()
    assert happy_hour.time_ranges.filter(weekday=2, from_hour=datetime.time(0), to_hour=to_hour).exists()
    _assert_view_get(rf, happy_hour, shop, staff_user)  # Viewing the edit should also still work


@pytest.mark.django_db
def test_happy_hours_admin_edit_view_just_before_midnight(rf, staff_user, admin_user):
    shop = factories.get_default_shop()
    shop.staff_members.add(staff_user)
    factories.get_shop(identifier="shop2", enabled=True)
    assert Shop.objects.count() == 2

    # Staff user gets shop automatically
    from_hour = datetime.time(hour=21, minute=0)
    to_hour = datetime.time(hour=23, minute=58)
    data = {"name": "Happiest Hour Before Twilight", "weekdays": [1], "from_hour": from_hour, "to_hour": to_hour}  # Tue
    request = apply_request_middleware(rf.post("/", data=data), user=staff_user, shop=shop)
    set_shop(request, shop)
    assert request.shop == shop
    view_func = HappyHourEditView.as_view()
    response = view_func(request)
    if hasattr(response, "render"):
        response.render()

    assert response.status_code == 302

    happy_hour = HappyHour.objects.first()
    assert happy_hour is not None
    assert happy_hour.shop == shop
    assert happy_hour.time_ranges.count() == 1
    assert happy_hour.time_ranges.filter(weekday=1).exists()
    assert happy_hour.time_ranges.filter(weekday=1, from_hour=from_hour, to_hour=datetime.time(23, 58)).exists()
    _assert_view_get(rf, happy_hour, shop, staff_user)  # Viewing the edit should also still work


@pytest.mark.django_db
def test_happy_hours_admin_edit_form_set_discount(rf, staff_user, admin_user):
    shop = factories.get_default_shop()
    shop.staff_members.add(staff_user)

    discount = Discount.objects.create(shop=shop)
    data = {
        "name": "Happiest Hour 2pm",
        "weekdays": [6],  # Sun
        "from_hour": datetime.time(hour=14, minute=0),
        "to_hour": datetime.time(hour=14, minute=0),
    }
    request = apply_request_middleware(rf.post("/", data=data), user=staff_user, shop=shop)
    set_shop(request, shop)
    assert request.shop == shop
    view_func = HappyHourEditView.as_view()
    response = view_func(request)
    if hasattr(response, "render"):
        response.render()

    assert response.status_code == 302
    happy_hour = HappyHour.objects.first()
    data.update({"discounts": [discount]})
    request = apply_request_middleware(rf.post("/", data=data), user=staff_user, shop=shop)
    view_func = HappyHourEditView.as_view()
    response = view_func(request, pk=happy_hour.pk)
    if hasattr(response, "render"):
        response.render()

    assert response.status_code == 302
    discount = Discount.objects.first()

    request = apply_request_middleware(rf.post("/", data=data), user=staff_user, shop=shop)
    view_func = HappyHourEditView.as_view()
    response = view_func(request, pk=happy_hour.pk)
    if hasattr(response, "render"):
        response.render()

    assert response.status_code == 302
    discount = Discount.objects.first()
    assert discount.happy_hours.count() == 1
    assert discount.happy_hours.first() == happy_hour


def _test_happy_hours_list_view(rf, index):
    shop = factories.get_shop(identifier="shop%s" % index, enabled=True)
    staff_user = factories.create_random_user(is_staff=True)
    shop.staff_members.add(staff_user)

    HappyHour.objects.create(name="After Work %s" % index, shop=shop)

    view_func = HappyHourListView.as_view()
    request = apply_request_middleware(
        rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=staff_user, shop=shop
    )
    set_shop(request, shop)
    response = view_func(request)
    if hasattr(response, "render"):
        response.render()
    assert response.status_code == 200

    view_instance = HappyHourListView()
    view_instance.request = request
    assert request.shop == shop
    assert view_instance.get_queryset().count() == 1

    data = json.loads(view_instance.get(request).content.decode("UTF-8"))
    assert len(data["items"]) == 1


@pytest.mark.django_db
def test_discount_admin_list_view(rf, admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        for x in range(3):
            _test_happy_hours_list_view(rf, x)

        # Superuser gets same data as shop staff
        shop = Shop.objects.exclude(identifier=factories.DEFAULT_IDENTIFIER).order_by("?").first()
        request = apply_request_middleware(
            rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=admin_user, shop=shop
        )
        set_shop(request, shop)
        view_instance = HappyHourListView()
        view_instance.request = request
        data = json.loads(view_instance.get(request).content.decode("UTF-8"))
        assert len(data["items"]) == 1


def _test_happy_hours_delete_view(rf, index):
    shop = factories.get_shop(identifier="shop%s" % index, enabled=True)
    staff_user = factories.create_random_user(is_staff=True)
    shop.staff_members.add(staff_user)
    happy_hour_name = "The Hour %s" % index
    happy_hour = HappyHour.objects.create(name=happy_hour_name, shop=shop)
    HappyHour.objects.create(name="Extra Hour %s" % index, shop=shop)

    assert HappyHour.objects.filter(name=happy_hour_name).exists()
    view_func = HappyHourDeleteView.as_view()
    request = apply_request_middleware(rf.post("/"), user=staff_user, shop=shop)
    set_shop(request, shop)
    response = view_func(request, pk=happy_hour.pk)
    if hasattr(response, "render"):
        response.render()
    assert response.status_code == 302
    assert not HappyHour.objects.filter(name=happy_hour_name).exists()

    # Make sure that this staff can't remove other people discounts
    other_exceptions = HappyHour.objects.exclude(shop=shop)
    exception_count = other_exceptions.count()
    for happy_hour in other_exceptions:
        view_func = HappyHourDeleteView.as_view()
        request = apply_request_middleware(rf.post("/"), user=staff_user, shop=shop)
        set_shop(request, shop)
        with pytest.raises(Http404):
            response = view_func(request, pk=happy_hour.pk)
            if hasattr(response, "render"):
                response.render()

    assert exception_count == HappyHour.objects.exclude(shop=shop).count()


@pytest.mark.django_db
def test_happy_hours_admin_delete_view(rf):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        for x in range(3):
            _test_happy_hours_delete_view(rf, x)
