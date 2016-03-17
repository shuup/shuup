# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shoop.xtheme.plugins.snippets import GenericSnippetsPlugin


class SnippetsPlugin(GenericSnippetsPlugin):
    identifier = "classic_gray.snippets"
    name = _("Snippets")
