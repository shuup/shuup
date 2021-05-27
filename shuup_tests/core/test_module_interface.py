# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest

from shuup.core.models import Supplier


@pytest.mark.django_db
def test_module_interface_for_scandinavian_letters(rf):
    supplier = Supplier.objects.create(identifier="module_interface_test", name="ääääööööååå")

    assert isinstance(supplier, Supplier)
    assert not supplier.modules
    assert "%r" % supplier

    supplier.delete()
