# -*- coding: utf-8 -*-
from django.forms import formset_factory
import pytest
from shoop.admin.modules.products.views.variation.simple_variation_forms import SimpleVariationChildForm, SimpleVariationChildFormSet
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
