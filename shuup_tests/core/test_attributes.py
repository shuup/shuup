# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime
import pytest
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings
from django.utils.translation import get_language

from shuup.core.models import (
    Attribute,
    AttributeChoiceOption,
    AttributeType,
    AttributeVisibility,
    Product,
    ProductAttribute,
)
from shuup.core.models._attributes import NoSuchAttributeHere
from shuup.testing.factories import ATTR_SPECS, create_product, get_default_attribute_set, get_default_product


def _populate_applied_attribute(aa):
    if aa.attribute.type == AttributeType.BOOLEAN:
        aa.value = True
        aa.save()
        assert aa.value is True, "Truth works"
        assert aa.untranslated_string_value == "1", "Integer attributes save string representations"
        aa.value = not 42  # (but it could be something else)
        aa.save()
        assert aa.value is False, "Lies work"
        assert aa.untranslated_string_value == "0", "Integer attributes save string representations"
        aa.value = None
        aa.save()
        assert aa.value is None, "None works"
        assert aa.untranslated_string_value == "", "Boolean saves None"
        return

    if aa.attribute.type == AttributeType.INTEGER:
        aa.value = 320.51
        aa.save()
        assert aa.value == 320, "Integer attributes get rounded down"
        assert aa.untranslated_string_value == "320", "Integer attributes save string representations"
        return

    if aa.attribute.type == AttributeType.DECIMAL:
        aa.value = Decimal("0.636")  # Surface pressure of Mars
        aa.save()
        assert aa.value * 1000 == 636, "Decimals work like they should"
        assert aa.untranslated_string_value == "0.636", "Decimal attributes save string representations"
        return

    if aa.attribute.type == AttributeType.TIMEDELTA:
        aa.value = 86400
        aa.save()
        assert aa.value.days == 1, "86,400 seconds is one day"
        assert aa.untranslated_string_value == "86400", "Timedeltas are seconds as strings"

        aa.value = datetime.timedelta(days=4)
        aa.save()
        assert aa.value.days == 4, "4 days remain as 4 days"
        assert aa.untranslated_string_value == "345600", "Timedeltas are still seconds as strings"
        return

    if aa.attribute.type == AttributeType.UNTRANSLATED_STRING:
        aa.value = "Dog Hello"
        aa.save()
        assert aa.value == "Dog Hello", "Untranslated strings work"
        assert aa.untranslated_string_value == "Dog Hello", "Untranslated strings work"
        return

    if aa.attribute.type == AttributeType.TRANSLATED_STRING:
        assert aa.attribute.is_translated
        with override_settings(LANGUAGES=[(x, x) for x in ("en", "fi", "ga", "ja")]):
            versions = {
                "en": "science fiction",
                "fi": "tieteiskirjallisuus",
                "ga": "ficsean eolaíochta",
                "ja": "空想科学小説",
            }
            for language_code, text in versions.items():
                aa.set_current_language(language_code)
                aa.value = text
                aa.save()
                assert aa.value == text, "Translated strings work"
            for language_code, text in versions.items():
                assert aa.safe_translation_getter("translated_string_value", language_code=language_code) == text, (
                    "%s translation is safe" % language_code
                )

            aa.set_current_language("xx")
            assert aa.value == "", "untranslated version yields an empty string"

        return

    if aa.attribute.type == AttributeType.DATE:
        aa.value = "2014-01-01"
        assert aa.value == datetime.date(2014, 1, 1), "Date parsing works"
        assert aa.untranslated_string_value == "2014-01-01", "Dates are saved as strings"
        return

    if aa.attribute.type == AttributeType.DATETIME:
        with pytest.raises(TypeError):
            aa.value = "yesterday"
        dt = datetime.datetime(1997, 8, 12, 14)
        aa.value = dt
        assert aa.value.toordinal() == 729248, "Date assignment works"
        assert aa.value.time().hour == 14, "The clock still works"
        assert aa.untranslated_string_value == dt.isoformat(), "Datetimes are saved as strings too"
        return

    if aa.attribute.type == AttributeType.CHOICES:
        option_a = AttributeChoiceOption.objects.create(attribute=aa.attribute, name="Option A")
        option_b = AttributeChoiceOption.objects.create(attribute=aa.attribute, name="Option B")
        option_c = AttributeChoiceOption.objects.create(attribute=aa.attribute, name="Option C")
        aa.value = [option_a, option_b.pk, option_c.name]
        aa.save()
        assert aa.value == "Option A; Option B; Option C"
        return

    raise NotImplementedError("Error! Not implemented: populating %s" % aa.attribute.type)  # pragma: no cover


@pytest.mark.django_db
def test_applied_attributes():
    product = get_default_product()
    for spec in ATTR_SPECS:  # This loop sets each attribute twice. That's okay.
        attr = Attribute.objects.get(identifier=spec["identifier"])
        pa, _ = ProductAttribute.objects.get_or_create(product=product, attribute=attr)
        _populate_applied_attribute(pa)
        pa.save()
        if not attr.is_translated:
            product.set_attribute_value(attr.identifier, pa.value)

    assert product.get_attribute_value("bogomips") == 320, "integer attribute loaded neatly"
    product.set_attribute_value("bogomips", 480)
    assert product.get_attribute_value("bogomips") == 480, "integer attribute updated neatly"
    Product.cache_attributes_for_targets(
        applied_attr_cls=ProductAttribute,
        targets=[product],
        attribute_identifiers=[a["identifier"] for a in ATTR_SPECS],
        language=get_language(),
    )
    assert (
        get_language(),
        "bogomips",
    ) in product._attr_cache, "integer attribute in cache"
    assert product.get_attribute_value("bogomips") == 480, "integer attribute value in cache"
    assert (
        product.get_attribute_value("ba:gelmips", default="Britta") == "Britta"
    ), "non-existent attributes return default value"
    assert product._attr_cache[(get_language(), "ba:gelmips")] is NoSuchAttributeHere, "cache miss saved"
    attr_info = product.get_all_attribute_info(
        language=get_language(), visibility_mode=AttributeVisibility.SHOW_ON_PRODUCT_PAGE
    )
    assert set(attr_info.keys()) <= set(
        a["identifier"] for a in ATTR_SPECS
    ), "get_all_attribute_info gets all attribute info"


@pytest.mark.django_db
def test_get_set_attribute():
    product = create_product("ATTR_TEST")
    product.set_attribute_value("awesome", True)
    product.set_attribute_value("bogomips", 10000)
    product.set_attribute_value("bogomips", None)
    product.set_attribute_value("author", None)
    product.set_attribute_value("genre", "Kenre", "fi")

    choice_attr = Attribute.objects.get(identifier="list_choices")
    AttributeChoiceOption.objects.create(attribute=choice_attr, name="Option A")
    AttributeChoiceOption.objects.create(attribute=choice_attr, name="Option B")
    AttributeChoiceOption.objects.create(attribute=choice_attr, name="Option C")

    product.set_attribute_value("list_choices", ["Option A", "Option C"])

    with pytest.raises(ValueError):
        product.set_attribute_value("genre", "Kenre")

    with pytest.raises(ObjectDoesNotExist):
        product.set_attribute_value("keppi", "stick")


@pytest.mark.django_db
def test_get_choice_attribute():
    product = create_product("ATTR_TEST")
    attribute = Attribute.objects.create(
        identifier="choices", type=AttributeType.CHOICES, min_choices=1, max_choices=10, name="Options"
    )
    product.type.attributes.add(attribute)
    option1 = AttributeChoiceOption.objects.create(attribute=attribute, name="Option 1")
    option2 = AttributeChoiceOption.objects.create(attribute=attribute, name="Option 2")
    option3 = AttributeChoiceOption.objects.create(attribute=attribute, name="Option 3")

    product.set_attribute_value("choices", ["Option 1", "Option 3"])
    assert product.get_attribute_value("choices") == [option1, option3]
    applied_attribute = product.attributes.get(attribute=attribute)

    applied_attribute.value = "Option 1"
    applied_attribute.save()
    assert applied_attribute.value == "Option 1"
    assert product.get_attribute_value("choices") == [option1]

    applied_attribute.value = "Option 2; Option 3"
    applied_attribute.save()
    assert applied_attribute.value == "Option 2; Option 3"
    assert product.get_attribute_value("choices") == [option2, option3]


def test_saving_invalid_attribute():
    with pytest.raises(ValueError):
        Attribute(identifier=None).save()
