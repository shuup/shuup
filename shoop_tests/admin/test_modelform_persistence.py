# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import six
from django.forms.models import ModelForm
from django.utils import translation

from shoop.core.models import Product
from shoop.core.models.products import StockBehavior
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class TestMultiProductForm(MultiLanguageModelForm):
    class Meta:
        model = Product
        fields = (
            "barcode",  # Regular field
            "stock_behavior",  # Enum field
            "name"
        )

class TestSingleProductForm(ModelForm):
    class Meta:
        model = Product
        fields = (
            "barcode",  # Regular field
            "stock_behavior",  # Enum field
        )

@pytest.mark.django_db
def test_modelform_persistence():
    with translation.override("en"):
        test_product = Product(barcode="666", stock_behavior=StockBehavior.STOCKED)
        test_product.set_current_language("en")
        test_product.name = "foo"
        frm = TestMultiProductForm(languages=["en"], instance=test_product, default_language="en")
        assert frm["barcode"].value() == test_product.barcode
        stock_behavior_field = Product._meta.get_field_by_name("stock_behavior")[0]
        assert stock_behavior_field.to_python(frm["stock_behavior"].value()) is test_product.stock_behavior
        assert 'value="1" selected="selected"' in six.text_type(frm["stock_behavior"].as_widget())
        assert frm.initial["name"] == test_product.name
