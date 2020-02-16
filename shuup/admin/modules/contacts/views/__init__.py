# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from .detail import ContactDetailView
from .edit import ContactEditView
from .list import ContactListView
from .mass_edit import ContactGroupMassEditView, ContactMassEditView
from .reset import ContactResetPasswordView

__all__ = [
    "ContactListView",
    "ContactDetailView",
    "ContactResetPasswordView",
    "ContactEditView",
    "ContactGroupMassEditView",
    "ContactMassEditView",
]
