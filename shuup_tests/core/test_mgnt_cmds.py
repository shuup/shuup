# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings
from django.core.management import call_command
from django.utils.translation import activate
from faker import Faker
from jinja2.filters import do_striptags
from six import StringIO

from shuup.core.models import Product
from shuup.testing.factories import create_product


@pytest.mark.django_db
def test_extract_products_shortdescription():
    activate("en")
    out = StringIO()

    html_description1 = "<b>a HTML description</b>"
    product1 = create_product("p1", description=html_description1)

    html_description2 = '<p class="what">another HTML description</p>'
    product2 = create_product("p2", description=html_description2)

    faker = Faker()
    long_description = faker.sentence(nb_words=150, variable_nb_words=True)
    product3 = create_product("p3", description=long_description)

    for lang, _ in settings.LANGUAGES:
        product2.set_current_language(lang)
        product2.description = html_description2
        product2.save()

    call_command("shuup_extract_products_shortdescription", stdout=out)

    product1 = Product.objects.get(pk=product1.pk)
    product2 = Product.objects.get(pk=product2.pk)
    product3 = Product.objects.get(pk=product3.pk)

    assert product1.short_description == do_striptags(html_description1)

    for lang, _ in settings.LANGUAGES:
        product2.set_current_language(lang)
        assert product2.short_description == do_striptags(html_description2)

    assert product3.short_description == long_description[:150]

    assert "Done." in out.getvalue()
