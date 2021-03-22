# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import six
from django.forms.models import ModelForm
from django.utils import translation

from shuup.core.models import Product
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


class MultiProductForm(MultiLanguageModelForm):
    class Meta:
        model = Product
        fields = ("barcode", "name")  # Regular field


class SingleProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ("barcode",)  # Regular field


@pytest.mark.django_db
def test_modelform_persistence():
    with translation.override("en"):
        test_product = Product(barcode="666")
        test_product.set_current_language("en")
        test_product.name = "foo"
        frm = MultiProductForm(languages=["en"], instance=test_product, default_language="en")
        assert frm["barcode"].value() == test_product.barcode
        assert frm.initial["name"] == test_product.name
