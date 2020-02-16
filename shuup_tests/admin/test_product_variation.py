# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import six
from django.forms import formset_factory

from shuup.admin.modules.products.forms import (
    SimpleVariationChildForm, SimpleVariationChildFormSet,
    VariableVariationChildrenForm
)
from shuup.core.excs import ImpossibleProductModeException
from shuup.testing.factories import create_product
from shuup.utils.excs import Problem
from shuup_tests.utils import printable_gibberish
from shuup_tests.utils.forms import get_form_data


@pytest.mark.django_db
def test_simple_children_formset():
    FormSet = formset_factory(SimpleVariationChildForm, SimpleVariationChildFormSet, extra=5, can_delete=True)
    parent = create_product(printable_gibberish())
    child = create_product(printable_gibberish())

    # No links yet
    formset = FormSet(parent_product=parent)
    assert formset.initial_form_count() == 0  # No children yet

    # Save a link
    data = dict(get_form_data(formset, True), **{"form-0-child": child.pk})
    formset = FormSet(parent_product=parent, data=data)
    formset.save()
    assert parent.variation_children.filter(pk=child.pk).exists()  # Got link'd!

    # Remove the link
    formset = FormSet(parent_product=parent)
    assert formset.initial_form_count() == 1  # Got the child here
    data = dict(get_form_data(formset, True), **{"form-0-DELETE": "1"})
    formset = FormSet(parent_product=parent, data=data)
    formset.save()
    assert not parent.variation_children.exists()  # Got unlinked


@pytest.mark.django_db
def test_impossible_simple_variation():
    FormSet = formset_factory(SimpleVariationChildForm, SimpleVariationChildFormSet, extra=5, can_delete=True)
    parent = create_product(printable_gibberish())
    child = create_product(printable_gibberish())
    grandchild = create_product(printable_gibberish())
    grandchild.link_to_parent(child)
    assert child.variation_children.exists()

    formset = FormSet(parent_product=parent)
    data = dict(get_form_data(formset, True), **{"form-0-child": child.pk})
    formset = FormSet(parent_product=parent, data=data)
    assert formset.is_valid()  # It's technically valid, but...
    with pytest.raises(Problem) as ei:
        formset.save()

    if six.PY3:  # Can only test inner exceptions on Py3. Ah well.
        inner_exc = ei.value.__context__
        assert isinstance(inner_exc, ImpossibleProductModeException)
        assert inner_exc.code == "multilevel"


@pytest.mark.django_db
def test_variable_variation_form():
    var1 = printable_gibberish()
    var2 = printable_gibberish()
    parent = create_product(printable_gibberish())
    for a in range(4):
        for b in range(3):
            child = create_product(printable_gibberish())
            child.link_to_parent(parent, variables={var1: a, var2: b})
    assert parent.variation_children.count() == 4 * 3

    form = VariableVariationChildrenForm(parent_product=parent)
    assert len(form.fields) == 12
    # TODO: Improve this test?
