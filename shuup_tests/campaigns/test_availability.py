# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
# test that admin actually saves catalog
import datetime
import pytest
import pytz
from django.db.models import Q

from shuup.campaigns.models import CatalogCampaign
from shuup.testing.factories import get_default_shop


def get_datetimes():
    past_datetime = datetime.datetime.now() - datetime.timedelta(days=2)
    future_datetime = datetime.datetime.now() + datetime.timedelta(days=2)
    return past_datetime.replace(tzinfo=pytz.UTC), future_datetime.replace(tzinfo=pytz.UTC)


@pytest.mark.django_db
def test_availability():
    shop = get_default_shop()
    campaign = CatalogCampaign.objects.create(name="test", active=False, shop=shop)

    assert not campaign.is_available()
    assert not CatalogCampaign.objects.available(shop).exists()

    campaign.active = True
    campaign.save()

    assert campaign.is_available()
    assert CatalogCampaign.objects.available(shop).exists()

    # test both start and end set
    past_datetime, future_datetime = get_datetimes()

    campaign.start_datetime = past_datetime
    campaign.end_datetime = future_datetime
    campaign.save()

    assert campaign.is_available()
    assert CatalogCampaign.objects.available(shop).exists()

    campaign.end_datetime = past_datetime
    campaign.save()

    assert not campaign.is_available()
    assert not CatalogCampaign.objects.available(shop).exists()

    # start date in past, no end, exists
    campaign.end_datetime = None
    campaign.save()

    assert campaign.is_available()
    assert CatalogCampaign.objects.available(shop).exists()

    # campaign starts in future, exists
    campaign.start_datetime = future_datetime
    campaign.save()

    assert not campaign.is_available()
    assert not CatalogCampaign.objects.available(shop).exists()

    # end in past, no start date, no match
    campaign.start_datetime = None
    campaign.end_datetime = past_datetime
    campaign.save()
    assert not campaign.is_available()
    assert not CatalogCampaign.objects.available(shop).exists()

    # end in future, no start date, match
    campaign.end_datetime = future_datetime
    campaign.save()
    assert campaign.is_available()
    assert CatalogCampaign.objects.available(shop).exists()
