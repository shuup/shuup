# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.db import transaction

from shuup.admin.modules.categories import CategoryModule
from shuup.admin.modules.categories.views.edit import CategoryBaseForm
from shuup.testing.factories import CategoryFactory
from shuup_tests.utils import empty_iterable
from shuup_tests.utils.forms import get_form_data


@pytest.mark.django_db
def test_category_module_search(rf):
    cm = CategoryModule()
    category = CategoryFactory()
    request = rf.get("/")
    assert not empty_iterable(cm.get_search_results(request, query=category.identifier))
    assert empty_iterable(cm.get_search_results(request, query="k"))


@pytest.mark.django_db
def test_category_form_saving(rf):
    with transaction.atomic():
        category = CategoryFactory()
        form_kwargs = dict(instance=category, languages=("sw",), default_language="sw")
        form = CategoryBaseForm(**form_kwargs)
        assert isinstance(form, CategoryBaseForm)
        form_data = get_form_data(form, prepared=True)
        for lang, field_map in form.trans_name_map.items():
            for dst_field in field_map.values():
                form_data[form.add_prefix(dst_field)] = "IJWEHGWOHKSL"
        form_kwargs["data"] = form_data
        form = CategoryBaseForm(**form_kwargs)
        form.full_clean()
        form.save()
        category = form.instance
        category.set_current_language("sw")
        assert category.name == "IJWEHGWOHKSL"
