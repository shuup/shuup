# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.xtheme.admin_module.views._snippet import SnippetDeleteView, SnippetEditView, SnippetListView
from shuup.xtheme.admin_module.views._theme import (
    ActivationForm,
    TemplateView,
    ThemeConfigDetailView,
    ThemeConfigView,
    ThemeGuideTemplateView,
    ThemeWizardPane,
)

__all__ = [
    "ActivationForm",
    "SnippetDeleteView",
    "SnippetEditView",
    "SnippetListView",
    "TemplateView",
    "ThemeConfigDetailView",
    "ThemeConfigView",
    "ThemeGuideTemplateView",
    "ThemeWizardPane",
]
