# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import hashlib
import itertools
from collections import defaultdict

import six
from django.db import models
from django.utils.encoding import (
    force_bytes, force_text, python_2_unicode_compatible
)
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from parler.models import TranslatableModel, TranslatedFields

from shuup.core.fields import InternalIdentifierField
from shuup.utils.models import SortableMixin


class ProductVariationLinkStatus(Enum):
    INVISIBLE = 0
    VISIBLE = 1

    class Labels:
        INVISIBLE = _('invisible')
        VISIBLE = _('visible')


@python_2_unicode_compatible
class ProductVariationVariable(TranslatableModel, SortableMixin):
    product = models.ForeignKey(
        "Product", related_name='variation_variables', on_delete=models.CASCADE, verbose_name=_("product"))
    identifier = InternalIdentifierField(unique=False)
    translations = TranslatedFields(
        name=models.CharField(max_length=128, verbose_name=_('name')),
    )

    class Meta:
        verbose_name = _('variation variable')
        verbose_name_plural = _('variation variables')
        unique_together = (("product", "identifier", ),)
        ordering = ('ordering', )

    def __str__(self):
        return self.safe_translation_getter("name") or self.identifier or repr(self)


@python_2_unicode_compatible
class ProductVariationVariableValue(TranslatableModel, SortableMixin):
    variable = models.ForeignKey(
        ProductVariationVariable, related_name='values', on_delete=models.CASCADE, verbose_name=_("variation variable"))
    identifier = InternalIdentifierField(unique=False)

    translations = TranslatedFields(
        value=models.CharField(max_length=128, verbose_name=_('value')),
    )

    class Meta:
        verbose_name = _('variation value')
        verbose_name_plural = _('variation values')
        unique_together = (("variable", "identifier", ),)
        ordering = ('ordering', )

    def __str__(self):
        return self.safe_translation_getter("value") or self.identifier or repr(self)


class ProductVariationResult(models.Model):
    product = models.ForeignKey(
        "Product", related_name='variation_result_supers', on_delete=models.CASCADE, verbose_name=_("product"))
    combination_hash = models.CharField(max_length=40, unique=True, db_index=True, verbose_name=_("combination hash"))
    result = models.ForeignKey(
        "Product", related_name='variation_result_subs', on_delete=models.CASCADE, verbose_name=_("result"))
    status = EnumIntegerField(
        ProductVariationLinkStatus, db_index=True, default=ProductVariationLinkStatus.VISIBLE, verbose_name=_("status"))

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
    :type parent: shuup.core.models.Product
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


def get_all_available_combinations(product):
    results = product.get_available_variation_results()
    values_by_variable = defaultdict(list)
    values = (
        ProductVariationVariableValue.objects.filter(variable__product=product)
        .prefetch_related("variable").order_by("ordering")
    )
    for val in values:
        values_by_variable[val.variable].append(val)

    if not values_by_variable:
        return

    variables_list, value_sets_list = zip(*values_by_variable.items())

    for value_set_combo in itertools.product(*value_sets_list):
        variable_to_value = dict(zip(variables_list, value_set_combo))
        sorted_variable_to_value = sorted(variable_to_value.items(), key=lambda varval: varval[0].ordering)
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
