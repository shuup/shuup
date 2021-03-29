# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.contenttypes.models import ContentType
from django.http.response import Http404

from shuup.admin.shop_provider import SHOP_SESSION_KEY
from shuup.admin.utils.urls import get_model_url
from shuup.admin.views.edit import EditObjectView, NoModelUrl
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup.utils.excs import Problem


def _get_edit_object_view(rf, view, model_name, object_id, user, shop, mode=None):
    data = {"model": model_name, "id": object_id or ""}
    if mode:
        data["mode"] = mode
    request = apply_request_middleware(rf.get(reverse("shuup_admin:edit"), data), user=user, shop=shop)
    return view(request)


@pytest.mark.parametrize(
    "creator_fn",
    [
        lambda: factories.create_product("sku", factories.get_default_shop(), factories.get_default_supplier()),
        lambda: factories.create_random_person(),
        lambda: factories.create_random_company(),
        lambda: factories.create_random_order(
            customer=factories.create_random_person(),
            products=[factories.create_product("p", factories.get_default_shop(), factories.get_default_supplier())],
        ),
        lambda: factories.create_random_user(),
    ],
)
@pytest.mark.django_db
def test_edit_object_view(rf, admin_user, creator_fn):
    shop = factories.get_default_shop()
    view = EditObjectView.as_view()
    object_instance = creator_fn()
    model = ".".join(ContentType.objects.get_for_model(object_instance).natural_key())

    # correct shop
    response = _get_edit_object_view(rf, view, model, object_instance.id, admin_user, shop)
    assert response.status_code == 302

    urls = []

    try:
        urls.append(get_model_url(object_instance, kind="edit", user=admin_user, shop=shop))
    except NoModelUrl:
        pass

    try:
        urls.append(get_model_url(object_instance, kind="detail", user=admin_user, shop=shop))
    except NoModelUrl:
        pass

    assert response.url in urls

    # pass the mode query parameter
    response = _get_edit_object_view(rf, view, model, object_instance.id, admin_user, shop, mode="test")
    assert response.status_code == 302
    assert "mode=test" in response.url


@pytest.mark.django_db
def test_edit_object_view_no_permissions(rf):
    user = factories.create_random_user("en", is_staff=True)
    shop = factories.get_default_shop()
    shop.staff_members.add(user)

    view = EditObjectView.as_view()
    product = factories.create_product("p1", shop, factories.get_default_supplier())
    model = ".".join(ContentType.objects.get_for_model(product).natural_key())

    # no permission
    with pytest.raises(Problem) as error:
        _get_edit_object_view(rf, view, model, product.id, user, shop)
    assert "You do not have the required permission" in str(error)


@pytest.mark.django_db
def test_edit_object_view_errors(rf, admin_user):
    shop = factories.get_default_shop()
    view = EditObjectView.as_view()

    # missing params
    response = view(apply_request_middleware(rf.get(reverse("shuup_admin:edit")), user=admin_user, shop=shop))
    assert response.status_code == 400
    assert "Invalid object" in response.content.decode("utf-8")

    # invalid model
    response = _get_edit_object_view(rf, view, ".", None, admin_user, shop)
    assert response.status_code == 400
    assert "Invalid object" in response.content.decode("utf-8")

    # invalid object ID
    product = factories.create_product("p1", shop, factories.get_default_supplier())
    model = ".".join(ContentType.objects.get_for_model(product).natural_key())
    with pytest.raises(Http404) as error:
        _get_edit_object_view(rf, view, model, product.id + 10, admin_user, shop)
    assert "Object not found" in str(error)

    # object has no admin url
    from shuup.core.models import ConfigurationItem

    config = ConfigurationItem.objects.create(shop=shop, key="test", value={"value": 123})
    model = ".".join(ContentType.objects.get_for_model(config).natural_key())
    with pytest.raises(Http404) as error:
        _get_edit_object_view(rf, view, model, config.id, admin_user, shop)
    assert "Object not found" in str(error)
