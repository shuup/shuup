# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from .detail import ContactDetailView
from .edit import ContactEditView
from .list import ContactListView
from .reset import ContactResetPasswordView

__all__ = ["ContactListView", "ContactDetailView", "ContactResetPasswordView", "ContactEditView"]
