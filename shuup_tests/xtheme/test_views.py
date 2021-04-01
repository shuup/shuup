# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.testing import factories
from shuup.utils.excs import Problem
from shuup.xtheme.editing import is_edit_mode
from shuup.xtheme.views.command import command_dispatch
from shuup_tests.utils.faux_users import SuperUser


def test_edit_can_be_set_via_view(rf):
    request = rf.get("/")
    request.user = SuperUser()
    request.shop = factories.get_default_shop()
    request.session = {}
    request.POST = {"command": "edit_on"}
    command_dispatch(request)
    assert is_edit_mode(request)
    request.POST = {"command": "edit_off"}
    command_dispatch(request)
    assert not is_edit_mode(request)


def test_dispatch_view_kvetches_at_unknown_commands(rf):
    with pytest.raises(Problem):
        command_dispatch(rf.post("/"))
