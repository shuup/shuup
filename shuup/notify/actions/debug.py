# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.notify.base import Action, Binding, ConstantUse
from shuup.notify.typology import Text


class SetDebugFlag(Action):
    identifier = "set_debug_flag"
    flag_name = Binding("Flag Name", Text, constant_use=ConstantUse.CONSTANT_ONLY, default="debug")

    def execute(self, context):
        context.set(self.get_value(context, "flag_name"), True)
