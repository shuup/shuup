# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.notify import Context
from shoop.notify.actions import AddNotification
from shoop.notify.base import TemplatedBinding
from shoop.notify.enums import ConstantUse


def test_templated_binding_security():
    with pytest.raises(ValueError):
        tb = TemplatedBinding("x", constant_use=ConstantUse.VARIABLE_ONLY)

    with pytest.raises(ValueError):
        tb = TemplatedBinding("y", constant_use=ConstantUse.VARIABLE_OR_CONSTANT)


def test_templated_binding_syntax_errors_swallowed():
    tb = TemplatedBinding("z", constant_use=ConstantUse.CONSTANT_ONLY)
    assert tb.get_value(Context(), {"constant": "{{"}) == "{{"


def test_bind_verification():
    with pytest.raises(ValueError):
        AddNotification({})  # add_notification requires a binding for message
