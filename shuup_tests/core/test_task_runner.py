# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.core.tasks import run_task

def test_run_task():
    result = run_task("shuup.utils.text.snake_case", value="test ing")
    assert result == "test_ing"
