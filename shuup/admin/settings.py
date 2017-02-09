# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

"""
Settings of Shuup Admin.

See :ref:`apps-settings` (in :obj:`shuup.apps`) for general information
about the Shuup settings system.  Especially, when inventing settings of
your own, the :ref:`apps-naming-settings` section is an important read.
"""

#: Spec which defines a list of Wizard Panes to be shown in Shuup Admin
#: for Shuup initialization and configuration.
#:
#: Panes must be subclasses of `shuup.admin.views.WizardPane`.
#:
SHUUP_SETUP_WIZARD_PANE_SPEC = []

#: Whether the admin checks per object permissions for the views and lists
#:
SHUUP_CHECK_PER_OBJECT_PERMISSIONS = False
