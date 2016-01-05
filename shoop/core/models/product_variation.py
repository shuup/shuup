# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import hashlib
import itertools
from collections import defaultdict

import six
from django.db import models
from django.forms import Form, IntegerField, Select
from django.utils.encoding import (
    force_bytes, force_text, python_2_unicode_compatible
)
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from parler.models import TranslatableModel, TranslatedFields

from shoop.core.fields import InternalIdentifierField

__all__ = ("ProductVariationVariable", "ProductVariationVariableValue", "ProductVariationResult")


class ProductVariationLinkStatus(Enum):
    INVISIBLE = 0
    VISIBLE = 1

    class Labels:
        INVISIBLE = _('invisible')
        VISIBLE = _('visible')


@python_2_unicode_compatible
class ProductVariationVariable(TranslatableModel):
    product = models.ForeignKey("Product", related_name='variation_variables', on_delete=models.CASCADE)
    identifier = InternalIdentifierField(unique=False)
    translations = TranslatedFields(
        name=models.CharField(max_length=128, verbose_name=_('name')),
    )

    class Meta:
        verbose_name = _('variation variable')
        verbose_name_plural = _('variation variables')
        unique_together = (("product", "identifier", ),)

    def __str__(self):
        return self.safe_translation_getter("name") or self.identifier or repr(self)


@python_2_unicode_compatible
class ProductVariationVariableValue(TranslatableModel):
    variable = models.ForeignKey(ProductVariationVariable, related_name='values', on_delete=models.CASCADE)
    identifier = InternalIdentifierField(unique=False)

    translations = TranslatedFields(
        value=models.CharField(max_length=128, verbose_name=_('value')),
    )

    class Meta:
        verbose_name = _('variation value')
        verbose_name_plural = _('variation values')
        unique_together = (("variable", "identifier", ),)

    def __str__(self):
        return self.safe_translation_getter("value") or self.identifier or repr(self)


class ProductVariationResult(models.Model):
    product = models.ForeignKey("Product", related_name='variation_result_supers', on_delete=models.CASCADE)
    combination_hash = models.CharField(max_length=40, unique=True, db_index=True)
    result = models.ForeignKey("Product", related_name='variation_result_subs', on_delete=models.CASCADE)
    status = EnumIntegerField(ProductVariationLinkStatus, db_index=True, default=ProductVariationLinkStatus.VISIBLE)

    @classmethod
    def resolve(cls, parent_product, combination):
        pvr = cls.objects.filter(
            product=parent_product,
            combination_hash=hash_combination(combination),
            status=ProductVariationLinkStatus.VISIBLE
        ).first()
        if pvr:
            return pvr.result

    class Meta:
        verbose_name = _('variation result')
        verbose_name_plural = _('variation results')


def hash_combination(combination):
    """
    Calculate the combination hash for a given mapping of variable PKs to value PKs.

    :param combination: Combination dict {pvv_pk: pvvv_pk}
    :type combination: dict[int, int]
    :return: Hash string
    :rtype: str
    """
    bits = []

    for variable, value in six.iteritems(combination):
        if isinstance(variable, six.integer_types) and isinstance(value, six.integer_types):
            bits.append("%d=%d" % (variable, value))
        else:
            bits.append("%d=%d" % (variable.pk, value.pk))

    bits.sort()
    raw_combination = ",".join(bits)
    hashed_combination = hashlib.sha1(force_bytes(raw_combination)).hexdigest()
    return hashed_combination


def get_combination_hash_from_variable_mapping(parent, variables):
    """
    Create a combination hash from a mapping of variable identifiers to value identifiers.

    If variables and values with the given identifier do not exist, they are created on the go.

    :param parent: Parent product
    :type parent: shoop.core.models.products.Product
    :param variables: Dict of {variable identifier: value identifier} for complex variable linkage
    :type variables: dict
    :return: Combination hash
    :rtype: str
    """
    mapping = {}
    for variable_identifier, value_identifier in variables.items():
        variable, _ = ProductVariationVariable.objects.get_or_create(
            product=parent, identifier=force_text(variable_identifier)
        )
        value, _ = ProductVariationVariableValue.objects.get_or_create(
            variable=variable, identifier=force_text(value_identifier)
        )
        mapping[variable] = value
    return hash_combination(mapping)


def get_available_variation_results(product):
    """
    Get a dict of `combination_hash` to product ID of variable variation results.

    :param product: Parent product
    :type product: shoop.core.models.Product
    :return: Mapping of combination hashes to product IDs
    :rtype: dict[str, int]
    """
    return dict(
        ProductVariationResult.objects.filter(product=product).filter(status=1)
        .values_list("combination_hash", "result_id")
    )


def get_all_available_combinations(product):
    """
    Generate all available combinations of variation variables for the given product.

    If the product is not a variable variation parent, the iterator is empty.

    Because of possible combinatorial explosion this is a generator function.
    (For example 6 variables with 5 options each explodes to 15,625 combinations.)

    :param product: A variable variation parent product.
    :type product: shoop.core.models.Product
    :return: Iterable of combination information dicts.
    :rtype: Iterable<dict>
    """
    results = get_available_variation_results(product)
    values_by_variable = defaultdict(list)
    values = (
        ProductVariationVariableValue.objects.filter(variable__product=product)
        .prefetch_related("variable").order_by("pk")
    )
    for val in values:
        values_by_variable[val.variable].append(val)

    if not values_by_variable:
        return

    variables_list, value_sets_list = zip(*values_by_variable.items())

    for value_set_combo in itertools.product(*value_sets_list):
        variable_to_value = dict(zip(variables_list, value_set_combo))
        sorted_variable_to_value = sorted(variable_to_value.items(), key=lambda varval: varval[0].pk)
        text_description = ", ".join(sorted("%s: %s" % (var, val) for (var, val) in sorted_variable_to_value))
        sku_part = "-".join(slugify(force_text(val))[:6] for (var, val) in sorted_variable_to_value)
        hash = hash_combination(variable_to_value)
        yield {
            "variable_to_value": variable_to_value,
            "hash": hash,
            "text_description": text_description,
            "sku_part": sku_part,
            "result_product_pk": results.get(hash)
        }


def get_variation_selection_form(request, product):  # pragma: no cover
    # TODO: Does this belong here? Eliding from coverage meanwhile.
    variables = ProductVariationVariable.objects.filter(product=product).order_by("name").values_list("id", "name")
    values = defaultdict(list)
    for var_id, val_id, val in (
        ProductVariationVariableValue.objects.filter(variable__product=product)
        .values_list("variable_id", "id", "value")
    ):
        values[var_id].append((val_id, val))
    form = Form(data=request.POST if request.POST else None)
    for variable_id, variable_name in variables:
        var_values = sorted(values.get(variable_id, ()))
        form.fields["var_%d" % variable_id] = IntegerField(label=variable_name, widget=Select(choices=var_values))
    return form


def clear_variation(product):
    """
    Fully remove variation information from the given variation parent.

    :param product: Variation parent to not be a variation parent any longer.
    :type product: shoop.core.models.Product
    """
    simplify_variation(product)
    for child in product.variation_children.all():
        if child.variation_parent_id == product.pk:
            child.unlink_from_parent()
    product.verify_mode()
    product.save()


def simplify_variation(product):
    """
    Remove variation variables from the given variation parent, turning it
    into a simple variation (or a normal product, if it has no children).

    :param product: Variation parent to not be variable any longer.
    :type product: shoop.core.models.Product
    """
    ProductVariationVariable.objects.filter(product=product).delete()
    ProductVariationResult.objects.filter(product=product).delete()
    product.verify_mode()
    product.save()
