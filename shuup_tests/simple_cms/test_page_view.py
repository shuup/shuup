# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.http.response import Http404
from django.utils import translation

from shuup.core.models import ShopStatus
from shuup.simple_cms.models import Page
from shuup.simple_cms.views import PageView
from shuup.testing.factories import create_random_user, get_default_shop, get_shop
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import is_anonymous
from shuup_tests.simple_cms.utils import create_multilanguage_page, create_page


@pytest.mark.django_db
def test_anon_cant_see_invisible_page(rf):
    page = create_page(shop=get_default_shop(), available_from=None)
    get_default_shop()
    view_func = PageView.as_view()
    request = apply_request_middleware(rf.get("/"))
    assert is_anonymous(request.user)
    with pytest.raises(Http404):
        response = view_func(request, url=page.url)


@pytest.mark.django_db
def test_superuser_can_see_invisible_page(rf, admin_user):
    page = create_page(shop=get_default_shop(), available_from=None)
    view_func = PageView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view_func(request, url=page.url)
    response.render()
    assert "<h1>Bacon ipsum" in response.rendered_content


@pytest.mark.django_db
def test_owner_can_see_invisible_page(rf):
    user = create_random_user()
    page = create_page(shop=get_default_shop(), available_from=None)
    view_func = PageView.as_view()
    request = apply_request_middleware(rf.get("/"), user=user)
    with pytest.raises(Http404):
        response = view_func(request, url=page.url)

    page.created_by = user
    page.save()
    response = view_func(request, url=page.url)
    response.render()
    assert "<h1>Bacon ipsum" in response.rendered_content


@pytest.mark.django_db
def test_visible_page_has_right_content(rf):
    page = create_page(available_from=datetime.date(1988, 1, 1), shop=get_default_shop())
    view_func = PageView.as_view()
    request = apply_request_middleware(rf.get("/"))
    assert is_anonymous(request.user)
    response = view_func(request, url=page.url)
    response.render()
    assert "<h1>Bacon ipsum" in response.rendered_content


@pytest.mark.django_db
def test_page_different_shops(rf):
    shop1 = get_shop(status=ShopStatus.ENABLED, identifier="shop-1", name="Shop 1", domain="shop1")
    shop2 = get_shop(status=ShopStatus.ENABLED, identifier="shop-2", name="Shop 2", domain="shop2")

    # dreate page only for shop2
    page = create_page(available_from=datetime.date(1988, 1, 1), shop=shop2)
    view_func = PageView.as_view()

    request = apply_request_middleware(rf.get("/", HTTP_HOST=shop1.domain))
    with pytest.raises(Http404):
        response = view_func(request, url=page.url)

    request = apply_request_middleware(rf.get("/", HTTP_HOST=shop2.domain))
    response = view_func(request, url=page.url)
    assert response.status_code == 200
    response.render()
    assert "<h1>Bacon ipsum" in response.rendered_content


@pytest.mark.django_db
def test_multilanguage_page_get_by_url(rf):
    page = create_multilanguage_page(eternal=True, url="ham", shop=get_default_shop())
    page_id = page.pk
    # Test that using `translations__url` will be able to retrieve pages
    # regardless of translation
    for lang in ("fi", "en"):
        for url in ("ham-fi", "ham-en"):
            page = Page.objects.language(lang).filter(translations__url=url).get(pk=page_id)
            assert page.get_current_language() == lang


@pytest.mark.django_db
def test_multilanguage_page_redirect(rf):
    page = create_multilanguage_page(eternal=True, url="redirector", shop=get_default_shop())
    get_default_shop()
    view_func = PageView.as_view()
    request = apply_request_middleware(rf.get("/"))
    with translation.override("fi"):
        page.set_current_language("fi")
        finnish_url = page.url
        response = view_func(request, url=finnish_url)
        assert response.status_code == 200  # Using the Finnish URL works
        page.set_current_language("en")
        english_url = page.url
        response = view_func(request, url=english_url)
        assert response.status_code == 302  # Using the English URL - redirect to finnish
        assert finnish_url in response["location"]
        # page.delete()


@pytest.mark.django_db
def test_multilanguage_page_404_no_xlate(rf):
    # https://github.com/edoburu/django-parler/issues/50
    cache.clear()  # this is here, because parler cache is enabled and tests use same pk with page
    page = create_multilanguage_page(
        eternal=True, url="no_content", shop=get_default_shop(), languages=("udm",)
    )  # create page with udm language
    get_default_shop()
    request = apply_request_middleware(rf.get("/"))
    with translation.override("fi"):  # change language of the page to fi
        view_func = PageView.as_view()
        with pytest.raises(Http404):
            response = view_func(request, url="no_content-udm")  # Using Udmurt URL, but xlate is Finnish . . .
            assert response.status_code == 404  # ... should 404


@pytest.mark.django_db
def test_render_page_title(rf):
    page = create_page(render_title=False, available_from=datetime.date(1988, 1, 1), shop=get_default_shop())
    view_func = PageView.as_view()
    request = apply_request_middleware(rf.get("/"))
    response = view_func(request, url=page.url)
    response.render()
    soup = BeautifulSoup(response.content)
    title = soup.find("h1", class_="page-header").text
    assert title == "\n"


@pytest.mark.django_db
def test_page_permission_group(rf):
    shop = get_default_shop()
    page = create_page(available_from=datetime.date(1988, 1, 1), shop=shop)
    permitted_group = Group.objects.create(name="Permitted")
    page.available_permission_groups.add(permitted_group)
    view_func = PageView.as_view()

    # not available for anonymous
    request = apply_request_middleware(rf.get("/"))
    with pytest.raises(Http404):
        response = view_func(request, url=page.url)

    # not available for wrong user group
    user = create_random_user()
    request = apply_request_middleware(rf.get("/"), user=user)
    with pytest.raises(Http404):
        response = view_func(request, url=page.url)

    # available for correct user group
    user.groups.add(permitted_group)
    request = apply_request_middleware(rf.get("/"), user=user)
    response = view_func(request, url=page.url)
    assert response.status_code == 200
    response.render()
    assert "<h1>Bacon ipsum" in response.rendered_content
