# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.notify.actions import AddNotification
from shuup.notify.base import TemplatedBinding
from shuup.notify.enums import ConstantUse
from shuup.notify.script import Context


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
