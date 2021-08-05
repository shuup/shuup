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
from django.utils.timezone import now

from shuup.admin.shop_provider import set_shop
from shuup.core.models import Shop
from shuup.discounts.admin.views import ArchivedDiscountListView, DiscountDeleteView, DiscountEditView, DiscountListView
from shuup.discounts.models import Discount
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


def _assert_view_get(rf, instance, shop, user, raises_404=False):
    request = apply_request_middleware(rf.get("/"), user=user, shop=shop)
    set_shop(request, shop)
    view_func = DiscountEditView.as_view()
    if raises_404:
        with pytest.raises(Http404):
            view_func(request, pk=instance.pk)
    else:
        response = view_func(request, pk=instance.pk)
        assert response.status_code == 200


@pytest.mark.django_db
def test_discount_admin_edit_view(rf, staff_user, admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        shop = factories.get_default_shop()
        shop.staff_members.add(staff_user)
        factories.get_shop(identifier="shop2")
        assert Shop.objects.count() == 2

        # Staff user gets shop automatically
        product = factories.create_product("test", shop=shop)
        discount_percentage = 20
        data = {"product": product.pk, "discount_percentage": discount_percentage}
        request = apply_request_middleware(rf.post("/", data=data), user=staff_user, shop=shop)
        set_shop(request, shop)
        assert request.shop == shop
        view_func = DiscountEditView.as_view()
        response = view_func(request)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == 302
        discount1 = Discount.objects.first()
        assert discount1.shop == shop

        # Test with superuser and with different shop
        shop2 = factories.get_shop(enabled=True)
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user, shop=shop2)
        set_shop(request, shop2)
        view_func = DiscountEditView.as_view()
        response = view_func(request)
        assert response.status_code == 302
        assert Discount.objects.count() == 2

        discount2 = Discount.objects.exclude(id=discount1.pk).first()
        assert discount1 != discount2

        # Staff user can only view discount1 since that has the right shop
        _assert_view_get(rf, discount1, shop, staff_user)
        _assert_view_get(rf, discount2, shop, staff_user, True)

        # Superuser can see both if needed, but only when right shop is active
        _assert_view_get(rf, discount1, shop, admin_user)
        _assert_view_get(rf, discount2, shop, admin_user, True)
        _assert_view_get(rf, discount2, shop2, admin_user)


def _test_discount_list_view(rf, index):
    shop = factories.get_shop(identifier="shop%s" % index, enabled=True)
    staff_user = factories.create_random_user(is_staff=True)
    shop.staff_members.add(staff_user)

    discount1 = Discount.objects.create(identifier="discount_without_effects_%s" % index, shop=shop)
    discount2 = Discount.objects.create(
        shop=shop,
        identifier="discount_with_amount_value_only_%s" % index,
        discount_amount_value=20,
        start_datetime=now(),
        end_datetime=now() + datetime.timedelta(days=2),
    )
    discount3 = Discount.objects.create(
        shop=shop,
        identifier="discount_with_amount_and_discounted_price_%s" % index,
        discount_amount_value=20,
        discounted_price_value=4,
        start_datetime=now(),
        end_datetime=now() + datetime.timedelta(days=2),
    )
    discount4 = Discount.objects.create(
        shop=shop,
        identifier="test_with_discounted_price_and_percentage_%s" % index,
        discounted_price_value=4,
        discount_percentage=0.20,
        start_datetime=now(),
        end_datetime=now() + datetime.timedelta(days=2),
    )

    view_func = DiscountListView.as_view()
    request = apply_request_middleware(
        rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=staff_user, shop=shop
    )
    set_shop(request, shop)
    response = view_func(request)
    if hasattr(response, "render"):
        response.render()
    assert response.status_code == 200

    view_instance = DiscountListView()
    view_instance.request = request
    assert request.shop == shop
    assert view_instance.get_queryset().count() == 4

    data = json.loads(view_instance.get(request).content.decode("UTF-8"))
    assert len(data["items"]) == 4
    discount1_data = [item for item in data["items"] if item["_id"] == discount1.pk][0]
    assert discount1_data["discount_effect"] == "-"

    discount2_data = [item for item in data["items"] if item["_id"] == discount2.pk][0]
    assert len(discount2_data["discount_effect"].split(",")) == 1
    assert "20" in discount2_data["discount_effect"]

    discount3_data = [item for item in data["items"] if item["_id"] == discount3.pk][0]
    assert len(discount3_data["discount_effect"].split(",")) == 2
    assert "20" in discount3_data["discount_effect"]
    assert "4" in discount3_data["discount_effect"]

    discount4_data = [item for item in data["items"] if item["_id"] == discount4.pk][0]
    assert len(discount4_data["discount_effect"].split(",")) == 2
    assert "20" in discount4_data["discount_effect"]
    assert "4" in discount4_data["discount_effect"]


@pytest.mark.django_db
def test_discount_admin_list_view(rf, admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        for x in range(3):
            _test_discount_list_view(rf, x)

        # Superuser gets same data as shop staff
        shop = Shop.objects.exclude(identifier=factories.DEFAULT_IDENTIFIER).order_by("?").first()
        request = apply_request_middleware(
            rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=admin_user, shop=shop
        )
        set_shop(request, shop)
        view_instance = DiscountListView()
        view_instance.request = request
        data = json.loads(view_instance.get(request).content.decode("UTF-8"))
        assert len(data["items"]) == 4

        # In active 3 discounts to see that those are filtered out
        payload = {
            "action": "archive_discounts",
            "values": [discount.pk for discount in Discount.objects.filter(shop=shop).order_by("?")[:3]],
        }
        archive_request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
        set_shop(archive_request, shop)
        archive_request._body = json.dumps(payload).encode("UTF-8")
        view = DiscountListView.as_view()
        response = view(request=archive_request)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == 200
        assert Discount.objects.available(shop).count() == 1

        data = json.loads(view_instance.get(request).content.decode("UTF-8"))
        assert len(data["items"]) == 1

        # Archived list should now show 3 results
        archived_view_instance = ArchivedDiscountListView()
        archived_view_instance.request = request
        data = json.loads(archived_view_instance.get(request).content.decode("UTF-8"))
        assert len(data["items"]) == 3

        # Make sure rendering this archived discounts list works
        view_func = ArchivedDiscountListView.as_view()
        request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop)
        set_shop(request, shop)
        response = view_func(request)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == 200

        # Unarchive all discounts
        payload = {"action": "unarchive_discounts", "values": "all"}
        unarchive_request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
        set_shop(unarchive_request, shop)
        unarchive_request._body = json.dumps(payload).encode("UTF-8")
        view = ArchivedDiscountListView.as_view()
        response = view(request=unarchive_request)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == 200
        assert Discount.objects.available(shop).count() == 4

        # Re-archive all discounts
        payload = {"action": "archive_discounts", "values": "all"}
        archive_request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
        set_shop(archive_request, shop)
        archive_request._body = json.dumps(payload).encode("UTF-8")
        view = DiscountListView.as_view()
        response = view(request=archive_request)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == 200
        assert Discount.objects.available(shop).count() == 0

        # Unarchive just one discount
        payload = {
            "action": "unarchive_discounts",
            "values": [discount.pk for discount in Discount.objects.filter(shop=shop).order_by("?")[:1]],
        }
        unarchive_request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
        set_shop(unarchive_request, shop)
        unarchive_request._body = json.dumps(payload).encode("UTF-8")
        view = ArchivedDiscountListView.as_view()
        response = view(request=unarchive_request)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == 200
        assert Discount.objects.available(shop).count() == 1

        # Delete one archived discount
        payload = {
            "action": "delete_discounts",
            "values": [discount.pk for discount in Discount.objects.archived(shop).order_by("?")[:1]],
        }
        delete_request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
        set_shop(delete_request, shop)
        delete_request._body = json.dumps(payload).encode("UTF-8")
        view = ArchivedDiscountListView.as_view()
        response = view(request=delete_request)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == 200
        assert Discount.objects.filter(shop=shop).count() == 3

        # Delete all for this shop only
        payload = {"action": "delete_discounts", "values": "all"}
        delete_request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
        set_shop(delete_request, shop)
        delete_request._body = json.dumps(payload).encode("UTF-8")
        view = ArchivedDiscountListView.as_view()
        response = view(request=delete_request)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == 200
        assert Discount.objects.filter(shop=shop).count() == 1  # Since only archived can be deleted with mass action
        assert Discount.objects.available(shop).count() == 1
        assert Discount.objects.archived(shop).count() == 0
        assert Discount.objects.count() == 9


def _test_discount_delete_view(rf, index):
    shop = factories.get_shop(identifier="shop%s" % index, enabled=True)
    staff_user = factories.create_random_user(is_staff=True)
    shop.staff_members.add(staff_user)
    discount_identifier = "discount%s" % index
    discount = Discount.objects.create(identifier=discount_identifier, shop=shop)
    Discount.objects.create(identifier="extra_discount%s" % index, shop=shop)

    assert Discount.objects.filter(identifier=discount_identifier).exists()
    view_func = DiscountDeleteView.as_view()
    request = apply_request_middleware(rf.post("/"), user=staff_user, shop=shop)
    set_shop(request, shop)
    response = view_func(request, pk=discount.pk)
    if hasattr(response, "render"):
        response.render()
    assert response.status_code == 302
    assert not Discount.objects.filter(identifier=discount_identifier).exists()

    # Make sure that this staff can't remove other people discounts
    other_discounts = Discount.objects.exclude(shop=shop)
    discount_count = other_discounts.count()
    for discount in other_discounts:
        view_func = DiscountDeleteView.as_view()
        request = apply_request_middleware(rf.post("/"), user=staff_user, shop=shop)
        set_shop(request, shop)
        with pytest.raises(Http404):
            response = view_func(request, pk=discount.pk)
            if hasattr(response, "render"):
                response.render()

    assert discount_count == Discount.objects.exclude(shop=shop).count()


@pytest.mark.django_db
def test_discount_admin_delete_view(rf):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        for x in range(3):
            _test_discount_delete_view(rf, x)
