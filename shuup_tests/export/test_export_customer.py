# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import csv
import io
import pytest
from django.utils.html import strip_tags

from shuup.admin.modules.contacts.mass_actions import ExportContactsCSVAction
from shuup.admin.modules.contacts.views.list import ContactListView
from shuup.admin.modules.settings.view_settings import ViewSettings
from shuup.core.models import Contact
from shuup.testing.factories import create_random_person, get_default_staff_user
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_export_customer_sample(rf):
    # create input: shop, request to use in process(request, ids) method
    base_view = ExportContactsCSVAction()
    random_customer = create_random_person()

    request = apply_request_middleware(rf.get("/"), user=get_default_staff_user())
    view_instance = ContactListView()
    view_instance.request = request
    view_settings = ViewSettings(Contact, ContactListView.default_columns, view_instance)
    setting_cols = view_settings.columns

    customer_from_query = base_view.get_queryset(request, view_instance, [random_customer.pk])[0]
    assert customer_from_query.pk == random_customer.pk

    response = base_view.process(request, [random_customer.pk])
    assert response.status_code == 200

    content = response.content.decode("utf-8")
    cvs_reader = csv.reader(io.StringIO(content))
    body = list(cvs_reader)
    headers = body.pop(0)
    for dr in setting_cols:
        index = setting_cols.index(dr)
        assert (strip_tags(dr.get_display_value(view_settings.view_context, random_customer))) == body[0][0].split(";")[
            index
        ]

    assert len(view_settings.columns) == len(headers[0].split(";"))
