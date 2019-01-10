# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from shuup import configuration
from shuup.api.admin_module.forms import APIPermissionForm
from shuup.api.permissions import PermissionLevel
from shuup.core import cache


def setup_function(fn):
    cache.clear()


@pytest.mark.django_db
def test_permission_form():
    form_data = {}

    form = APIPermissionForm()

    # extract fields
    for field in form.fields.keys():
        # make sure that nothing is saved in configs
        assert configuration.get(None, field) is None

        # disable the API
        form_data[field] = PermissionLevel.DISABLED

    form = APIPermissionForm(data=form_data)
    form.save()

    # now check if the values were save
    for field in form.fields.keys():
        assert int(configuration.get(None, field)) == PermissionLevel.DISABLED
