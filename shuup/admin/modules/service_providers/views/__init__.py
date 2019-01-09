# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from ._delete import ServiceProviderDeleteView
from ._edit import ServiceProviderEditView
from ._list import ServiceProviderListView
from ._wizard import CarrierWizardPane, PaymentWizardPane

__all__ = [
    "ServiceProviderDeleteView",
    "ServiceProviderEditView",
    "ServiceProviderListView",
    "CarrierWizardPane",
    "PaymentWizardPane"
]
