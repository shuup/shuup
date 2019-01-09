# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.utils import update_module_attributes

from ._theme import override_current_theme_class

__all__ = [
    "override_current_theme_class",
]

update_module_attributes(__all__, __name__)
