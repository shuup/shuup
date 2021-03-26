# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings
from django.utils.text import slugify
from django.utils.translation import activate

from shuup.testing.factories import create_product, get_default_category


@pytest.mark.django_db
@override_settings(**{"LANGUAGES": (("en", "en"), ("fi", "fi")), "PARLER_DEFAULT_LANGUAGE_CODE": "fi"})
def test_generate_slugs_for_product():
    activate("en")
    product_name = "Some name"
    product = create_product(sku="1", **{"name": "Some name"})
    assert product.slug == slugify(product_name)

    # Test that slug is only generated when it's empty on save
    new_name = "Some new name"
    product.name = new_name
    product.save()
    assert product.slug == slugify(product_name), "Old slug"
    product.slug = ""
    product.save()
    assert product.slug == slugify(new_name), "New slug generated"

    # Check that slug is not generated to other languages
    with pytest.raises(ObjectDoesNotExist):
        translation = product.get_translation("fi")
        translation.refresh_from_db()  # If the translation object was returned from cache


@pytest.mark.django_db
@override_settings(**{"LANGUAGES": (("en", "en"), ("fi", "fi")), "PARLER_DEFAULT_LANGUAGE_CODE": "fi"})
def test_generate_slugs_for_category():
    activate("en")
    category = get_default_category()
    assert category.slug == slugify(category.name)
    default_slug = category.slug

    # Test that slug is only generated when it's empty on save
    new_name = "Some new cat name"
    category.name = new_name
    category.save()
    assert category.slug == default_slug, "Old slug"
    category.slug = ""
    category.save()
    assert category.slug == slugify(new_name), "New slug generated"

    # Check that slug is not generated to other languages
    with pytest.raises(ObjectDoesNotExist):
        translation = category.get_translation("fi")
        translation.refresh_from_db()  # If the translation object was returned from cache


@pytest.mark.django_db
@override_settings(**{"LANGUAGES": (("en", "en"), ("fi", "fi"), ("ja", "ja")), "PARLER_DEFAULT_LANGUAGE_CODE": "fi"})
def test_slug_is_generate_from_translation():
    activate("en")
    category = get_default_category()
    assert category.slug == slugify(category.name)
    default_slug = category.slug
    activate("fi")
    category.set_current_language("fi")
    name_fi = "Joku nimi"
    category.name = name_fi
    category.save()
    assert category.slug == slugify(name_fi)

    # Make sure english still have default slug
    activate("en")
    category.set_current_language("en")
    assert category.slug == default_slug

    # Make sure Japanese does not have translations generated
    # Check that slug is not generated to other languages
    with pytest.raises(ObjectDoesNotExist):
        translation = category.get_translation("ja")
        translation.refresh_from_db()  # If the translation object was returned from cache
