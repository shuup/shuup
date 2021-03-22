# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
# test that admin actually saves catalog
from __future__ import unicode_literals

import datetime
import pytest
import pytz
from django.test import override_settings

from shuup.apps.provides import override_provides
from shuup.campaigns.admin_module.form_parts import CatalogBaseFormPart
from shuup.campaigns.admin_module.views import CatalogCampaignEditView
from shuup.campaigns.models.campaigns import CatalogCampaign
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware

DEFAULT_CONDITION_FORMS = [
    "shuup.campaigns.admin_module.forms:ContactGroupConditionForm",
    "shuup.campaigns.admin_module.forms:ContactConditionForm",
]

DEFAULT_FILTER_FORMS = [
    "shuup.campaigns.admin_module.forms:ProductTypeFilterForm",
    "shuup.campaigns.admin_module.forms:ProductFilterForm",
    "shuup.campaigns.admin_module.forms:CategoryFilterForm",
]

DEFAULT_EFFECT_FORMS = [
    "shuup.campaigns.admin_module.forms:ProductDiscountAmountForm",
    "shuup.campaigns.admin_module.forms:ProductDiscountPercentageForm",
]


def get_form_parts(request, view, object):
    with override_provides("campaign_context_condition", DEFAULT_CONDITION_FORMS):
        with override_provides("campaign_catalog_filter", DEFAULT_FILTER_FORMS):
            with override_provides("campaign_product_discount_effect_form", DEFAULT_EFFECT_FORMS):
                initialized_view = view(request=request, kwargs={"pk": object.pk})
                return initialized_view.get_form_parts(object)


@pytest.mark.django_db
def test_admin_campaign_edit_view_works(rf, admin_user):
    shop = get_default_shop()
    view_func = CatalogCampaignEditView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    campaign = CatalogCampaign.objects.create(name="test campaign", active=True, shop=shop)
    response = view_func(request, pk=campaign.pk)
    assert campaign.name in response.rendered_content

    response = view_func(request, pk=None)
    assert response.rendered_content


@pytest.mark.django_db
def test_campaign_new_mode_view_formsets(rf, admin_user):
    view = CatalogCampaignEditView
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    form_parts = get_form_parts(request, view, view.model())
    assert len(form_parts) == 1
    assert issubclass(form_parts[0].__class__, CatalogBaseFormPart)


@pytest.mark.django_db
def test_campaign_edit_view_formsets(rf, admin_user):
    view = CatalogCampaignEditView
    shop = get_default_shop()
    object = CatalogCampaign.objects.create(name="test campaign", active=True, shop=shop)
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    form_parts = get_form_parts(request, view, object)
    # form parts should include forms  plus one for the base form
    assert len(form_parts) == (len(DEFAULT_CONDITION_FORMS) + len(DEFAULT_FILTER_FORMS) + len(DEFAULT_EFFECT_FORMS) + 1)


@pytest.mark.django_db
def test_campaign_creation(rf, admin_user):
    """
    To make things little bit more simple let's use only english as
    a language.
    """
    with override_settings(LANGUAGES=[("en", "en")]):
        view = CatalogCampaignEditView.as_view()
        data = {
            "base-name": "Test Campaign",
            "base-public_name__en": "Test Campaign",
            "base-shop": get_default_shop().id,
            "base-active": True,
            "base-basket_line_text": "Test campaign activated!",
        }
        campaigns_before = CatalogCampaign.objects.count()
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        response = view(request, pk=None)
        assert response.status_code in [200, 302]
        assert CatalogCampaign.objects.count() == (campaigns_before + 1)


@pytest.mark.django_db
def test_campaign_edit_save(rf, admin_user):
    """
    To make things little bit more simple let's use only english as
    a language.
    """
    with override_settings(LANGUAGES=[("en", "en")]):
        shop = get_default_shop()
        object = CatalogCampaign.objects.create(name="test campaign", active=True, shop=shop)
        object.save()
        view = CatalogCampaignEditView.as_view()
        new_name = "Test Campaign"
        new_end_datetime = datetime.datetime(year=2016, month=6, day=20)
        assert object.name != new_name
        assert object.end_datetime is None
        data = {
            "base-name": new_name,
            "base-public_name__en": "Test Campaign",
            "base-shop": get_default_shop().id,
            "base-active": True,
            "base-basket_line_text": "Test campaign activated!",
            "base-start_datetime": datetime.datetime(year=2016, month=6, day=19),
            "base-end_datetime": new_end_datetime,
        }
        methods_before = CatalogCampaign.objects.count()
        # Conditions, effects and effects is tested separately
        with override_provides("campaign_context_condition", []):
            with override_provides("campaign_catalog_filter", []):
                with override_provides("campaign_product_discount_effect_form", []):
                    request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
                    response = view(request, pk=object.pk)
                    assert response.status_code in [200, 302]

        assert CatalogCampaign.objects.count() == methods_before
        updated_object = CatalogCampaign.objects.get(pk=object.pk)
        assert updated_object.name == new_name
        assert updated_object.end_datetime == new_end_datetime.replace(tzinfo=pytz.UTC)


@pytest.mark.django_db
def test_campaign_end_date(rf, admin_user):
    """
    To make things little bit more simple let's use only english as
    a language.
    """
    with override_settings(LANGUAGES=[("en", "en")]):
        shop = get_default_shop()
        old_name = "test_campaign"
        object = CatalogCampaign.objects.create(name=old_name, active=True, shop=shop)
        object.save()
        view = CatalogCampaignEditView.as_view()
        new_name = "Test Campaign"
        assert object.name != new_name
        data = {
            "base-name": new_name,
            "base-public_name__en": "Test Campaign",
            "base-shop": get_default_shop().id,
            "base-active": True,
            "base-basket_line_text": "Test campaign activated!",
            "base-start_datetime": datetime.datetime(year=2016, month=6, day=19),
            "base-end_datetime": datetime.datetime(year=2016, month=6, day=10),
        }
        methods_before = CatalogCampaign.objects.count()
        # Conditions, effects and effects is tested separately
        with override_provides("campaign_context_condition", []):
            with override_provides("campaign_catalog_filter", []):
                with override_provides("campaign_product_discount_effect_form", []):
                    request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
                    response = view(request, pk=object.pk)
                    assert response.status_code in [200, 302]
                    content = response.render().content.decode("utf-8")
                    assert "Campaign end date can&#39;t be before a start date." in content
        assert CatalogCampaign.objects.count() == methods_before
        assert CatalogCampaign.objects.get(pk=object.pk).name == old_name
