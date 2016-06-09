# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import datetime

import pytest
from django.core.cache import cache
from django.http.response import Http404
from django.utils import translation

from shuup.simple_cms.models import Page
from shuup.simple_cms.views import PageView
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup_tests.simple_cms.utils import create_multilanguage_page, create_page


@pytest.mark.django_db
def test_anon_cant_see_invisible_page(rf):
    page = create_page()
    get_default_shop()
    view_func = PageView.as_view()
    request = apply_request_middleware(rf.get("/"))
    assert request.user.is_anonymous()
    with pytest.raises(Http404):
        response = view_func(request, url=page.url)


@pytest.mark.django_db
def test_superuser_can_see_invisible_page(rf, admin_user):
    page = create_page()
    get_default_shop()
    view_func = PageView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view_func(request, url=page.url)
    response.render()
    assert "<h1>Bacon ipsum" in response.rendered_content


@pytest.mark.django_db
def test_visible_page_has_right_content(rf):
    page = create_page(available_from=datetime.date(1988, 1, 1))
    get_default_shop()
    view_func = PageView.as_view()
    request = apply_request_middleware(rf.get("/"))
    assert request.user.is_anonymous()
    response = view_func(request, url=page.url)
    response.render()
    assert "<h1>Bacon ipsum" in response.rendered_content


@pytest.mark.django_db
def test_multilanguage_page_get_by_url(rf):
    page = create_multilanguage_page(eternal=True, url="ham")
    page_id = page.pk
    # Test that using `translations__url` will be able to retrieve pages
    # regardless of translation
    for lang in ("fi", "en"):
        for url in ("ham-fi", "ham-en"):
            page = Page.objects.language(lang).filter(translations__url=url).get(pk=page_id)
            assert page.get_current_language() == lang


@pytest.mark.django_db
def test_multilanguage_page_redirect(rf):
    page = create_multilanguage_page(eternal=True, url="redirector")
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
    page = create_multilanguage_page(eternal=True, url="no_content",
                                     languages=("udm",))  # create page with udm language
    get_default_shop()
    request = apply_request_middleware(rf.get("/"))
    with translation.override("fi"):  # change language of the page to fi
        view_func = PageView.as_view()
        with pytest.raises(Http404):
            response = view_func(request, url="no_content-udm")  # Using Udmurt URL, but xlate is Finnish . . .
            assert response.status_code == 404  # ... should 404
