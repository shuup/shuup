# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.db import IntegrityError

from shoop.social_media.models import SocialMediaLink, SocialMediaLinkType


@pytest.mark.django_db
def test_social_media_link():
    type = SocialMediaLinkType.TWITTER
    url = "http://www.twitter.com"

    SocialMediaLink.objects.create(type=type, url=url)
    assert len(list(SocialMediaLink.objects.all())) == 1


@pytest.mark.django_db
def test_type_required():
    url = "http://www.twitter.com"

    with pytest.raises(IntegrityError) as error_info:
        SocialMediaLink.objects.create(type=None, url=url)


@pytest.mark.django_db
def test_url_required():
    type = SocialMediaLinkType.TWITTER

    with pytest.raises(IntegrityError) as error_info:
        SocialMediaLink.objects.create(type=type, url=None)


@pytest.mark.django_db
def test_ordering():
    type_1 = SocialMediaLinkType.TWITTER
    type_2 = SocialMediaLinkType.FACEBOOK
    url_1 = "http://www.twitter.com"
    url_2 = "http://www.facebook.com"

    # Check that links are properly ordered
    link_1 = SocialMediaLink.objects.create(type=type_1, url=url_1, ordering=1)
    link_2 = SocialMediaLink.objects.create(type=type_2, url=url_1, ordering=2)
    assert list(SocialMediaLink.objects.all()) == [link_1, link_2]

    # Change ordering and verify changes
    link_1.ordering = 3
    link_1.save()
    assert list(SocialMediaLink.objects.all()) == [link_2, link_1]
