# -*- coding: utf-8 -*-
import pytest

from shoop.social_media.models import SocialMediaLink, SocialMediaLinkType
from shoop.themes.classic_gray.plugins import SocialMediaLinksPlugin
from shoop_tests.front.fixtures import get_jinja_context


@pytest.mark.django_db
def test_social_media_links_plugin():
    context = get_jinja_context()
    type = SocialMediaLinkType.TWITTER
    url = "http://www.twitter.com"
    link = SocialMediaLink.objects.create(type=type, url=url)
    plugin = SocialMediaLinksPlugin({"links": [link.pk]})
    rendered = plugin.render(context)
    assert url in rendered
    assert link.icon_class_name in rendered
