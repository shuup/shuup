# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test.utils import override_settings

from shuup.admin.modules.manufacturers.views import ManufacturerDeleteView, ManufacturerEditView, ManufacturerListView
from shuup.admin.shop_provider import set_shop
from shuup.core.models import Manufacturer
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_manufacturer_admin_simple_shop(rf, staff_user, admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=False):
        shop1 = factories.get_default_shop()
        shop1.staff_members.add(staff_user)

        factories.get_shop(identifier="shop2")

        assert Manufacturer.objects.count() == 0

        # staff user
        request = apply_request_middleware(rf.post("/", data=dict(name="Manuf 1")), user=staff_user)
        view_func = ManufacturerEditView.as_view()
        response = view_func(request)
        assert response.status_code == 302
        assert Manufacturer.objects.first().shops.first() == shop1

        # superuser
        request = apply_request_middleware(rf.post("/", data=dict(name="Manuf 2")), user=admin_user)
        view_func = ManufacturerEditView.as_view()
        response = view_func(request)
        assert response.status_code == 302
        assert Manufacturer.objects.count() == 2
        assert Manufacturer.objects.last().shops.first() == shop1


@pytest.mark.django_db
def test_manufacturer_delete(rf, admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=False):
        shop1 = factories.get_default_shop()
        shop1.staff_members.add(admin_user)
        manu = Manufacturer.objects.create(name="manuf 1")
        manu.shops.add(shop1)
        manu.save()

        assert Manufacturer.objects.count() == 1

        request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop1)
        view_func = ManufacturerDeleteView.as_view()
        response = view_func(request, pk=manu.id)
        assert response.status_code == 302
        assert Manufacturer.objects.count() == 0


@pytest.mark.parametrize("superuser", [True, False])
def test_manufacturer_admin_multishop_shop(rf, staff_user, admin_user, superuser):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        shop1 = factories.get_shop(identifier="shop1", enabled=True)
        shop2 = factories.get_shop(identifier="shop2", enabled=True)
        shop1.staff_members.add(staff_user)
        shop2.staff_members.add(staff_user)

        assert Manufacturer.objects.count() == 0
        user = admin_user if superuser else staff_user

        request = apply_request_middleware(rf.post("/", data=dict(name="Manuf shop2")), user=user, shop=shop2)
        set_shop(request, shop2)
        view_func = ManufacturerEditView.as_view()
        response = view_func(request)
        assert response.status_code == 302

        if superuser:
            assert Manufacturer.objects.first().shops.count() == 0
        else:
            assert Manufacturer.objects.first().shops.first() == shop2

        for view_class in (ManufacturerEditView, ManufacturerListView):
            view_instance = view_class()
            view_instance.request = request

            assert view_instance.get_queryset().count() == 1
            if superuser:
                assert view_instance.get_queryset().first().shops.count() == 0
            else:
                assert view_instance.get_queryset().first().shops.count() == 1
                assert view_instance.get_queryset().first().shops.first() == shop2

        request = apply_request_middleware(rf.post("/", data=dict(name="Manuf shop1")), user=user, shop=shop1)
        set_shop(request, shop1)
        view_func = ManufacturerEditView.as_view()
        response = view_func(request)
        assert response.status_code == 302

        if superuser:
            assert Manufacturer.objects.last().shops.count() == 0
        else:
            assert Manufacturer.objects.last().shops.first() == shop1

        for view_class in (ManufacturerEditView, ManufacturerListView):
            view_instance = view_class()
            view_instance.request = request

            assert view_instance.get_queryset().count() == (2 if superuser else 1)

            if superuser:
                assert view_instance.get_queryset().first().shops.count() == 0
                assert view_instance.get_queryset().last().shops.count() == 0
            else:
                assert view_instance.get_queryset().first().shops.count() == 1
                assert view_instance.get_queryset().first().shops.first() == shop1
