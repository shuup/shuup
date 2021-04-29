# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.admin.modules.attributes.views.edit import AttributeEditView
from shuup.core.models import Attribute, AttributeType
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_attribute_edit_view(rf, admin_user):
    # create choices attribute
    shop = get_default_shop()
    data = {
        "base-name__en": "Attribute Name",
        "base-identifier": "attr-id",
        "base-searchable": "on",
        "base-type": AttributeType.CHOICES.value,
        "base-min_choices": 3,
        "base-max_choices": 10,
        "base-visibility_mode": 1,
        "base-ordering": 0,
    }
    request = apply_request_middleware(rf.post("/", data=data), shop=shop, user=admin_user)
    response = AttributeEditView.as_view()(request)
    assert response.status_code == 302
    attribute = Attribute.objects.get(identifier="attr-id")

    # Create the options on next save
    data.update(
        {
            "choice_options-TOTAL_FORMS": 2,
            "choice_options-INITIAL_FORMS": 0,
            "choice_options-MIN_NUM_FORMS": 0,
            "choice_options-MAX_NUM_FORMS": 100,
            "choice_options-0-name__en": "Option A",
            "choice_options-1-name__en": "Option B",
        }
    )
    request = apply_request_middleware(rf.post("/", data=data), shop=shop, user=admin_user)
    response = AttributeEditView.as_view()(request, pk=attribute.pk)
    assert response.status_code == 302

    options = list(sorted(attribute.choices.values_list("translations__name", flat=True)))
    assert options[0] == "Option A"
    assert options[1] == "Option B"

    options_ids = list(sorted(attribute.choices.values_list("pk", flat=True)))
    # change options
    data.update(
        {
            "choice_options-TOTAL_FORMS": 3,
            "choice_options-INITIAL_FORMS": 2,
            "choice_options-0-id": options_ids[0],
            "choice_options-0-name__en": "Option AZ",  # change name
            "choice_options-1-id": options_ids[1],
            "choice_options-1-DELETE": "on",  # delete option
            "choice_options-2-name__en": "Option C",  # new one
        }
    )
    request = apply_request_middleware(rf.post("/", data=data), shop=shop, user=admin_user)
    response = AttributeEditView.as_view()(request, pk=attribute.pk)
    assert response.status_code == 302

    attribute = Attribute.objects.get(identifier="attr-id")
    options = list(sorted(attribute.choices.values_list("translations__name", flat=True)))
    assert options[0] == "Option AZ"
    assert options[1] == "Option C"
    assert len(options) == 2
