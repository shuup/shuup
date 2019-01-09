#!/usr/bin/env python
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


class RemovedInShuup20Warning(PendingDeprecationWarning):
    pass


class RemovedFromShuupWarning(DeprecationWarning):
    pass


RemovedInFutureShuupWarning = RemovedInShuup20Warning
