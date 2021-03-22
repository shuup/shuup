# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.simple_cms.models import Page, PageOpenGraphType
from shuup.testing import factories
from shuup.testing.soup_utils import extract_form_fields
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
def test_opengrah_admin(admin_user):
    shop = factories.get_default_shop()
    client = SmartClient()
    client.login(username=admin_user.username, password="password")

    assert Page.objects.count() == 0
    response, soup = client.response_and_soup(reverse("shuup_admin:simple_cms.page.new"))
    assert response.status_code == 200

    # save simple page
    payload = {
        "base-title__en": "My Article",
        "base-url__en": "my-article",
        "base-available_from": "01/01/2018 00:00:00",
        "base-available_to": "01/01/2019 00:00:00",
        "base-content__en": "Some content here",
    }
    response = client.post(reverse("shuup_admin:simple_cms.page.new"), data=payload)
    assert response.status_code == 302
    assert Page.objects.count() == 1
    page = Page.objects.first()

    # check the rendered page in front
    page_url = reverse("shuup:cms_page", kwargs=dict(url=page.url))
    response, soup = client.response_and_soup(page_url)
    assert response.status_code == 200
    assert soup.find("meta", attrs={"property": "og:site_name", "content": shop.public_name})
    assert soup.find("meta", attrs={"property": "og:url"})
    assert soup.find("meta", attrs={"property": "og:title", "content": page.title})
    assert soup.find("meta", attrs={"property": "og:type", "content": "website"})
    assert soup.find("meta", attrs={"property": "og:description", "content": page.content})

    # set some open graph info
    random_image = factories.get_random_filer_image()
    payload.update(
        {
            "opengraph-title__en": "OG Title",
            "opengraph-tags__en": "OG Tags",
            "opengraph-section__en": "OG Section",
            "opengraph-description__en": "OG DESC",
            "opengraph-article_author__en": "OG AuthorName",
            "opengraph-og_type": PageOpenGraphType.Article.value,
            "opengraph-image": random_image.pk,
        }
    )

    response = client.post(reverse("shuup_admin:simple_cms.page.edit", kwargs=dict(pk=page.pk)), data=payload)
    assert response.status_code == 302
    assert Page.objects.count() == 1
    page = Page.objects.first()
    str(page.open_graph)  # just for coverage
    assert page.open_graph.title == payload["opengraph-title__en"]
    assert page.open_graph.tags == payload["opengraph-tags__en"]
    assert page.open_graph.section == payload["opengraph-section__en"]
    assert page.open_graph.description == payload["opengraph-description__en"]
    assert page.open_graph.og_type.value == payload["opengraph-og_type"]
    assert page.open_graph.article_author == payload["opengraph-article_author__en"]

    # check the rendered page in front
    page_url = reverse("shuup:cms_page", kwargs=dict(url=page.url))
    response, soup = client.response_and_soup(page_url)
    assert response.status_code == 200
    assert soup.find("meta", attrs={"property": "og:title", "content": payload["opengraph-title__en"]})
    assert soup.find("meta", attrs={"property": "og:type", "content": payload["opengraph-og_type"]})
    assert soup.find("meta", attrs={"property": "og:description", "content": payload["opengraph-description__en"]})
    assert soup.find("meta", attrs={"property": "og:type", "content": payload["opengraph-og_type"]})
    assert soup.find("meta", attrs={"property": "article:tag", "content": payload["opengraph-tags__en"]})
    assert soup.find("meta", attrs={"property": "article:section", "content": payload["opengraph-section__en"]})
    assert soup.find("meta", attrs={"property": "article:author", "content": payload["opengraph-article_author__en"]})
    assert soup.find("meta", attrs={"property": "article:modified_time", "content": page.modified_on.isoformat()})
    assert soup.find("meta", attrs={"property": "article:published_time", "content": page.available_from.isoformat()})
    assert soup.find("meta", attrs={"property": "article:expiration_time", "content": page.available_to.isoformat()})
    img_node = soup.find("meta", attrs={"property": "og:image"})
    assert img_node.attrs["content"].endswith(random_image.url)
