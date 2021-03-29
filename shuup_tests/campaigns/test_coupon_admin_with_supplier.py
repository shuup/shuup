# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
# test that admin actually saves catalog
import json
import pytest
from bs4 import BeautifulSoup
from django.http.response import Http404
from django.test import override_settings
from django.utils.translation import activate

from shuup.admin.supplier_provider import get_supplier
from shuup.admin.views.select import MultiselectAjaxView
from shuup.apps.provides import override_provides
from shuup.campaigns.admin_module.views import CouponEditView, CouponListView
from shuup.campaigns.models import Coupon
from shuup.core.models import Supplier
from shuup.testing.factories import create_random_user, get_default_shop
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_coupon_edit_view_works_with_supplier(rf, admin_user):
    shop = get_default_shop()
    supplier = Supplier.objects.create(identifier=admin_user.username)
    view_func = CouponEditView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    coupon = Coupon.objects.create(code="HORSESHOW123", active=True, shop=shop)
    response = view_func(request, pk=coupon.pk)
    assert coupon.code in response.rendered_content

    response = view_func(request, pk=None)
    assert response.rendered_content
    soup = BeautifulSoup(response.rendered_content)
    assert soup.find("select", {"id": "id_supplier"})

    supplier_provider = "shuup.testing.supplier_provider.UsernameSupplierProvider"
    with override_settings(SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC=supplier_provider):
        assert get_supplier(request) == supplier
        response = view_func(request, pk=None)
        assert response.rendered_content
        soup = BeautifulSoup(response.rendered_content)
        assert not soup.find("select", {"id": "id_supplier"})


@pytest.mark.django_db
def test_coupon_creation_for_supplier(rf, admin_user):
    """
    To make things little bit more simple let's use only english as
    a language.
    """
    shop = get_default_shop()
    supplier = Supplier.objects.create(identifier=admin_user.username)

    another_superuser = create_random_user(is_superuser=True, is_staff=True)
    supplier2 = Supplier.objects.create(identifier=another_superuser.username)

    supplier_provider = "shuup.testing.supplier_provider.UsernameSupplierProvider"
    with override_settings(LANGUAGES=[("en", "en")]):
        with override_settings(SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC=supplier_provider):
            view = CouponEditView.as_view()
            data = {"code": "OK", "active": True, "shop": shop.pk}
            coupons_before = Coupon.objects.count()
            request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
            assert get_supplier(request) == supplier
            response = view(request, pk=None)
            assert response.status_code in [200, 302]
            assert Coupon.objects.count() == (coupons_before + 1)

            new_coupon = Coupon.objects.filter(supplier=supplier).first()
            assert new_coupon

            # Another superuser shouldn't see this campaign
            request = apply_request_middleware(rf.post("/", data=data), user=another_superuser)
            assert get_supplier(request) == supplier2
            with pytest.raises(Http404):
                response = view(request, pk=new_coupon.pk)


def test_coupon_list_for_suppliers(rf, admin_user):
    """
    To make things little bit more simple let's use only english as
    a language.
    """
    shop = get_default_shop()

    superuser1 = create_random_user(is_superuser=True, is_staff=True)
    supplier1 = Supplier.objects.create(identifier=superuser1.username)

    superuser2 = create_random_user(is_superuser=True, is_staff=True)
    supplier2 = Supplier.objects.create(identifier=superuser2.username)

    supplier_provider = "shuup.testing.supplier_provider.UsernameSupplierProvider"
    with override_settings(LANGUAGES=[("en", "en")]):
        with override_settings(SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC=supplier_provider):
            code1 = Coupon.objects.create(code="1", active=True, shop=shop, supplier=supplier1)
            code2 = Coupon.objects.create(code="2", active=True, shop=shop, supplier=supplier2)

            view = CouponListView()
            request = apply_request_middleware(rf.get("/"), user=superuser1, shop=shop)
            assert get_supplier(request) == supplier1
            view.request = request
            assert code1 in view.get_queryset()
            assert code2 not in view.get_queryset()

            request = apply_request_middleware(rf.get("/"), user=superuser2, shop=shop)
            assert get_supplier(request) == supplier2
            view.request = request
            assert code1 not in view.get_queryset()
            assert code2 in view.get_queryset()

            # And actual superuser not linked to any supplier can see all like he should
            request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop)
            assert get_supplier(request) is None
            view.request = request
            assert code1 in view.get_queryset()
            assert code2 in view.get_queryset()


@pytest.mark.django_db
def test_coupon_with_supplier_filter(rf, admin_user):
    shop = get_default_shop()
    activate("en")
    view = MultiselectAjaxView.as_view()

    superuser1 = create_random_user(is_superuser=True, is_staff=True)
    supplier1 = Supplier.objects.create(identifier=superuser1.username)
    superuser2 = create_random_user(is_superuser=True, is_staff=True)
    supplier2 = Supplier.objects.create(identifier=superuser2.username)

    supplier_provider = "shuup.testing.supplier_provider.UsernameSupplierProvider"
    with override_settings(SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC=supplier_provider):
        code = Coupon.objects.create(code="LEAFS", active=True, shop=shop, supplier=supplier1)
        results = _get_search_results(rf, view, "campaigns.Coupon", "LEAFS", superuser1)
        assert len(results) == 1
        assert results[0].get("id") == code.id
        assert results[0].get("name") == code.code

        results = _get_search_results(rf, view, "campaigns.Coupon", "LEAFS", superuser2)
        assert len(results) == 0


def _get_search_results(rf, view, model_name, search_str, user, search_mode=None, sales_units=None, shop=None):
    data = {"model": model_name, "search": search_str}
    if search_mode:
        data.update({"searchMode": search_mode})

    if sales_units:
        data.update({"salesUnits": sales_units})

    if shop:
        data.update({"shop": shop.pk})

    request = apply_request_middleware(rf.get("sa/search", data), user=user)
    response = view(request)
    assert response.status_code == 200
    return json.loads(response.content.decode("utf-8")).get("results")
