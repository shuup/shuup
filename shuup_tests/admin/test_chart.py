# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.admin.dashboard.charts import Chart


def test_chart_is_abstract_enough():
    with pytest.raises(TypeError):
        Chart("Derp").get_config()
