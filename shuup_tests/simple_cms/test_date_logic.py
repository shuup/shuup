# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
import pytest
from django.utils.timezone import now

from shuup.simple_cms.models import Page
from shuup.testing.factories import get_default_shop
from shuup_tests.simple_cms.utils import create_page


@pytest.mark.django_db
def test_none_dates_page_not_visible():
    # create page that is not anymore visible
    page = create_page(shop=get_default_shop(), available_from=None)

    assert not Page.objects.visible(get_default_shop()).filter(pk=page.pk).exists()
    assert not page.is_visible()


@pytest.mark.django_db
def test_past_page_not_visible():
    today = now()
    page = create_page(
        available_from=(today - datetime.timedelta(days=2)),
        available_to=(today - datetime.timedelta(days=1)),
        shop=get_default_shop(),
    )
    assert not Page.objects.visible(get_default_shop()).filter(pk=page.pk).exists()
    assert not page.is_visible()


@pytest.mark.django_db
def test_future_page_not_visible():
    today = now()
    page = create_page(
        available_from=(today + datetime.timedelta(days=1)),
        available_to=(today + datetime.timedelta(days=2)),
        shop=get_default_shop(),
    )
    assert not Page.objects.visible(get_default_shop()).filter(pk=page.pk).exists()
    assert not page.is_visible()


@pytest.mark.django_db
def test_current_page_is_visible():
    today = now()
    page = create_page(available_from=today, available_to=today, shop=get_default_shop())

    assert Page.objects.visible(get_default_shop(), today).filter(pk=page.pk).exists()
    assert page.is_visible(today)


@pytest.mark.django_db
def test_page_without_visibility_end_is_visible():
    today = now()
    page = create_page(available_from=today, available_to=None, shop=get_default_shop())

    assert Page.objects.visible(get_default_shop(), today).filter(pk=page.pk).exists()
    assert page.is_visible(today)
