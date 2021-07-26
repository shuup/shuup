# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup
from django import forms
from django.utils.encoding import force_text
from django.utils.translation import activate

from shuup.admin.forms.fields import WeekdayField, WeekdaysSelectMultiple
from shuup.admin.modules.product_types.views import ProductTypeEditView
from shuup.core.models import Attribute, AttributeType, ProductType
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_objectSelectField(rf, admin_user):
    activate("en")
    attr1 = Attribute.objects.create(type=AttributeType.INTEGER, identifier="attr-1", name="Attribute 1")
    attr2 = Attribute.objects.create(type=AttributeType.INTEGER, identifier="attr-2", name="Attribute 2")
    product_type = ProductType.objects.create(name="Test product type")
    product_type.attributes.add(attr1)
    product_type.attributes.add(attr2)

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = ProductTypeEditView.as_view()(request, pk=product_type.pk)
    assert response.status_code == 200

    response.render()
    content_soup = BeautifulSoup(response.content, "lxml")

    options_names = [option.text for option in content_soup.findAll("option")]
    options_values = [int(option.attrs["value"]) for option in content_soup.findAll("option")]
    assert attr1.name in options_names
    assert attr2.name in options_names
    assert attr1.id in options_values
    assert attr2.id in options_values


@pytest.mark.django_db
def test_WeekdayField(rf, admin_user):
    activate("en")

    class TestForm(forms.Form):
        weekdays = WeekdayField()

    form = TestForm(data={"weekdays": [1, 2, 3]})
    assert form.is_valid()
    assert form.fields["weekdays"].to_python([1, 2, 3]) == ["1", "2", "3"]

    soup = BeautifulSoup(force_text(form), "lxml")
    selected_options = soup.find_all("option", {"selected": True})
    non_selected_options = soup.find_all("option", {"selected": False})
    assert [opt.attrs["value"] for opt in selected_options] == ["1", "2", "3"]
    assert [opt.attrs["value"] for opt in non_selected_options] == ["0", "4", "5", "6"]

    assert WeekdaysSelectMultiple().format_value("1,2,3") == ["1", "2", "3"]
    assert WeekdaysSelectMultiple().format_value("123") == ["123"]
    assert WeekdaysSelectMultiple().format_value(1) == ["1"]
