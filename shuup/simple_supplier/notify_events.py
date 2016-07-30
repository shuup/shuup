# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.notify import Event, Variable
from shuup.notify.typology import Model


class AlertLimitReached(Event):
    identifier = "alert_limit_reached"

    supplier = Variable("Supplier", type=Model("shuup.Supplier"))
    product = Variable("Product", type=Model("shuup.Product"))
