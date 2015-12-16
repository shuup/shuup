# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.admin.dashboard.charts import Chart


def test_chart_is_abstract_enough():
    with pytest.raises(TypeError):
        Chart("Derp").get_config()
