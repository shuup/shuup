# -*- coding: utf-8 -*-
from django.forms import formset_factory
import pytest
from shoop.admin.modules.products.views.variation.simple_variation_forms import SimpleVariationChildForm, SimpleVariationChildFormSet
from shoop.admin.modules.products.views.variation.variable_variation_forms import VariableVariationChildrenForm
from shoop.core.models.product_variation import ProductVariationVariable, ProductVariationVariableValue
from shoop.testing.factories import create_product
from shoop_tests.utils import printable_gibberish
from shoop_tests.utils.forms import get_form_data


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
