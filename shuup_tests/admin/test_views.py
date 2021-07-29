# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest
import six
from bs4 import BeautifulSoup
from django.test import override_settings
from django.test.client import Client
from django.utils.encoding import force_text
from django.utils.translation import activate
from mock import patch

from shuup.admin.modules.products.views import ProductEditView
from shuup.admin.utils.tour import is_tour_complete
from shuup.apps.provides import override_provides
from shuup.core.models import Product, ProductCatalogPrice, Shop, ShopProduct, ShopProductVisibility, ShopStatus
from shuup.testing.factories import (
    CategoryFactory,
    create_product,
    create_random_order,
    create_random_person,
    get_default_category,
    get_default_product,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.soup_utils import extract_form_fields
from shuup.testing.utils import apply_request_middleware
from shuup.utils.importing import load
from shuup_tests.utils import atomic_commit_mock


@pytest.mark.parametrize(
    "class_spec",
    [
        "shuup.admin.modules.categories.views.list:CategoryListView",
        "shuup.admin.modules.contacts.views:ContactListView",
        "shuup.admin.modules.orders.views:OrderListView",
        "shuup.admin.modules.products.views:ProductListView",
        "shuup.admin.modules.users.views:UserListView",
        "shuup.campaigns.admin_module.views.BasketCampaignListView",
        "shuup.campaigns.admin_module.views.CouponListView",
        "shuup.campaigns.admin_module.views.CatalogCampaignListView",
        "shuup.admin.modules.contact_groups.views.ContactGroupListView",
        "shuup.gdpr.admin_module.views.GDPRView",
        "shuup.admin.modules.contact_group_price_display.views.ContactGroupPriceDisplayListView",
        "shuup.admin.modules.permission_groups.views.PermissionGroupListView",
        "shuup.admin.modules.settings.views.SystemSettingsView",
    ],
)
@pytest.mark.django_db
def test_list_view(rf, class_spec, admin_user):
    get_default_shop()
    view = load(class_spec).as_view()

    # normal request
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request)
    assert response.status_code == 200

    # picotable request
    request = apply_request_middleware(rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=admin_user)
    response = view(request)
    assert 200 <= response.status_code < 300


def random_order():
    # These are prerequisites for random orders
    contact = create_random_person()
    product = get_default_product()
    return create_random_order(contact, [product])


@pytest.mark.parametrize(
    "model_and_class",
    [
        (get_default_category, "shuup.admin.modules.categories.views:CategoryEditView"),
        (create_random_person, "shuup.admin.modules.contacts.views:ContactDetailView"),
        (random_order, "shuup.admin.modules.orders.views:OrderDetailView"),
        (get_default_product, "shuup.admin.modules.products.views:ProductEditView"),
    ],
)
@pytest.mark.django_db
def test_detail_view(rf, admin_user, model_and_class):
    get_default_shop()  # obvious prerequisite
    model_func, class_spec = model_and_class
    model = model_func()
    view = load(class_spec).as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)

    if model_func == get_default_product:
        pk = model.shop_products.first().pk
    else:
        pk = model.pk

    response = view(request, pk=pk)
    if hasattr(response, "render"):
        response.render()
    assert 200 <= response.status_code < 300

    # request with iframe mode
    request = apply_request_middleware(rf.get("/", {"mode": "iframe"}), user=admin_user)
    response = view(request, pk=pk)
    if hasattr(response, "render"):
        response.render()
    assert 200 <= response.status_code < 300


@pytest.mark.parametrize(
    "extra_query_param,extra_query_value,expected_script",
    [
        ("", "", "parent.window.closeQuickIFrame()"),
        ("quick_add_target", "select2name", "parent.window.addToSelect2('select2name'"),
        ("quick_add_callback", "myTarget", "parent.window.myTarget("),
    ],
)
@pytest.mark.django_db
def test_iframe_mode(rf, admin_user, extra_query_param, extra_query_value, expected_script):
    get_default_shop()
    view = load("shuup.admin.modules.categories.views:CategoryEditView").as_view()

    request = apply_request_middleware(rf.get("/", {"mode": "iframe"}), user=admin_user)
    response = view(request)
    if hasattr(response, "render"):
        response.render()
    assert 200 <= response.status_code < 300

    content = force_text(response.content)
    post = extract_form_fields(BeautifulSoup(content, "lxml"))
    post.update({"base-name__en": "Name"})
    post.pop("base-image")

    # save iframe mode
    request = apply_request_middleware(rf.post("/", post), user=admin_user)
    request.GET = request.GET.copy()
    request.GET["mode"] = "iframe"

    if extra_query_param:
        request.GET[extra_query_param] = extra_query_value

    response = view(request)
    assert response.status_code == 302

    client = Client()
    client.login(username="admin", password="password")

    response = client.get(response.url)
    assert response.status_code == 200
    assert expected_script in force_text(response.content)


@pytest.mark.django_db
def test_edit_view_adding_messages_to_form_group(rf, admin_user):
    shop = get_default_shop()  # obvious prerequisite
    product = get_default_product()
    shop_product = product.get_shop_instance(shop)
    view = ProductEditView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request, pk=shop_product.pk)
    response.render()
    assert 200 <= response.status_code < 300

    assert ProductEditView.add_form_errors_as_messages

    content = force_text(response.content)
    post = extract_form_fields(BeautifulSoup(content, "lxml"))
    post_data = {
        # Error in the base form part
        "base-name__en": "",
    }
    post.update(post_data)
    request = apply_request_middleware(rf.post("/", post), user=admin_user)
    response = view(request, pk=shop_product.pk)

    errors = response.context_data["form"].errors

    assert "base" in errors
    assert "name__en" in errors["base"]


@pytest.mark.django_db
def test_product_edit_view(rf, admin_user, settings):
    shop = get_default_shop()  # obvious prerequisite
    shop.staff_members.add(admin_user)
    parent = create_product("ComplexVarParent", shop=shop, supplier=get_default_supplier())
    sizes = [("%sL" % ("X" * x)) for x in range(4)]
    for size in sizes:
        child = create_product("ComplexVarChild-%s" % size, shop=shop, supplier=get_default_supplier())
        child.link_to_parent(parent, variables={"size": size})
    shop_product = parent.get_shop_instance(shop)
    cat = CategoryFactory()

    assert not shop_product.categories.exists()
    assert not shop_product.primary_category

    view = ProductEditView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request, pk=shop_product.pk)
    response.render()

    content = force_text(response.content)
    post = extract_form_fields(BeautifulSoup(content, "lxml"))

    # Needed for Django 1.8 tests to pass
    post.update(
        {
            "shop1-default_price_value": "42",
            "images-TOTAL_FORMS": "0",
            "media-TOTAL_FORMS": "0",
            "base-name__fi": "test",
            "base-name__it": "test",
            "base-name__ja": "test",
            "base-name__pt-br": "test",
            "base-name__zh-hans": "test",
            "base-name__es": "test",
        }
    )

    post_data = {"shop1-primary_category": [], "shop1-categories": []}
    post.update(post_data)
    request = apply_request_middleware(rf.post("/", post), user=admin_user)
    response = view(request, pk=shop_product.pk)

    shop_product.refresh_from_db()
    assert not shop_product.categories.exists()
    assert not shop_product.primary_category

    post_data = {"shop1-default_price_value": 12, "shop1-primary_category": cat.pk, "shop1-categories": []}
    post.update(post_data)
    usable_post = {}
    for k, v in six.iteritems(post):
        if not k:
            continue
        if not post[k]:
            continue
        usable_post[k] = v

    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        request = apply_request_middleware(rf.post("/", usable_post), user=admin_user)
        response = view(request, pk=shop_product.pk)

    shop_product = ShopProduct.objects.first()
    assert shop_product.primary_category

    # the catalog price was indexed
    catalog_price = ProductCatalogPrice.objects.filter(shop=shop_product.shop, product=shop_product.product).first()
    assert catalog_price.price_value == shop_product.default_price_value

    if settings.SHUUP_AUTO_SHOP_PRODUCT_CATEGORIES:
        assert shop_product.categories.count() == 1
        assert shop_product.categories.first() == cat
    else:
        assert not shop_product.categories.count()

    assert shop_product.primary_category == cat

    post_data = {"shop1-primary_category": [], "shop1-categories": []}
    usable_post.update(post_data)

    request = apply_request_middleware(rf.post("/", usable_post), user=admin_user)
    response = view(request, pk=shop_product.pk)

    # empty again
    shop_product = ShopProduct.objects.first()
    assert not shop_product.categories.exists()
    assert not shop_product.primary_category

    post_data = {"shop1-primary_category": [], "shop1-categories": [cat.pk]}
    usable_post.update(post_data)

    request = apply_request_middleware(rf.post("/", usable_post), user=admin_user)
    response = view(request, pk=shop_product.pk)

    shop_product = ShopProduct.objects.first()
    assert shop_product.categories.count() == 1
    assert shop_product.categories.first() == cat
    if settings.SHUUP_AUTO_SHOP_PRODUCT_CATEGORIES:
        assert shop_product.primary_category == cat
    else:
        assert not shop_product.primary_category

    cat2 = CategoryFactory()

    post_data = {"shop1-primary_category": [], "shop1-categories": [cat.pk, cat2.pk]}
    usable_post.update(post_data)

    request = apply_request_middleware(rf.post("/", usable_post), user=admin_user)
    response = view(request, pk=shop_product.pk)

    shop_product = ShopProduct.objects.first()
    assert shop_product.categories.count() == 2
    assert cat in shop_product.categories.all()
    assert cat2 in shop_product.categories.all()
    if settings.SHUUP_AUTO_SHOP_PRODUCT_CATEGORIES:
        assert shop_product.primary_category == cat
    else:
        assert not shop_product.primary_category

    # Test for showing alert of validation issues
    view = ProductEditView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request, pk=shop_product.pk)
    response.render()
    content = force_text(response.content)
    soup = BeautifulSoup(content, "lxml")
    alert = soup.find_all("div", {"class": "validation-issues-alert"})
    assert not alert

    with override_provides(
        "admin_product_validator",
        ["shuup.testing.admin_product_validator:TestAdminProductValidator"],
    ):
        view = ProductEditView.as_view()
        request = apply_request_middleware(rf.get("/"), user=admin_user)
        response = view(request, pk=shop_product.pk)
        response.render()
        content = force_text(response.content)
        soup = BeautifulSoup(content, "lxml")
        alert = soup.find_all("div", {"class": "validation-issues-alert alert alert-danger"})
        assert alert
        alert_danger = soup.find_all("div", {"class": "alert-danger"})
        assert alert_danger
        alert = soup.find_all("div", {"class": "validation-issues-alert alert alert-warning"})
        alert_div = alert[0]
        strong = alert_div.find_all("strong")
        assert strong
        script = alert_div.find_all("script")
        assert not script


@pytest.mark.django_db
def test_product_edit_view_multishop(rf, admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        activate("en")
        product = create_product(sku="TEST-SKU-HAHA")
        shop_products = []

        for i in range(5):
            shop_name = "test%d" % i
            shop = Shop.objects.create(name=shop_name, domain=shop_name, status=ShopStatus.ENABLED)
            shop_products.append(
                ShopProduct.objects.create(product=product, shop=shop, visibility=ShopProductVisibility.ALWAYS_VISIBLE)
            )

        assert Product.objects.count() == 1

        view = ProductEditView.as_view()
        for shop_product in shop_products:
            request = apply_request_middleware(rf.get("/", HTTP_HOST=shop_product.shop.domain), user=admin_user)
            response = view(request, pk=shop_product.pk)
            assert response.status_code == 200
            response.render()
            content = force_text(response.content)
            assert product.sku in content


def test_menu_view(rf, admin_user):
    get_default_shop()  # obvious prerequisite
    view = load("shuup.admin.views.menu:MenuToggleView").as_view()
    request = apply_request_middleware(rf.post("/"), user=admin_user)

    assert "menu_open" not in request.session

    response = view(request)
    if hasattr(response, "render"):
        response.render()
    assert response.status_code == 200
    assert not request.session["menu_open"]  # Menu closed

    response = view(request)
    if hasattr(response, "render"):
        response.render()
    assert response.status_code == 200
    assert request.session["menu_open"]  # Menu open


def test_tour_view(rf, admin_user):
    shop = get_default_shop()
    assert is_tour_complete(shop, "home", admin_user) is False
    view = load("shuup.admin.views.tour:TourView").as_view()
    request = apply_request_middleware(rf.post("/", data={"tourKey": "home"}), user=admin_user)
    view(request)
    assert is_tour_complete(shop, "home", admin_user)
