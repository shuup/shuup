# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from .copy import CategoryCopyVisibilityView
from .delete import CategoryDeleteView
from .edit import CategoryEditView
from .list import CategoryListView

__all__ = ["CategoryEditView", "CategoryDeleteView", "CategoryListView", "CategoryCopyVisibilityView"]
