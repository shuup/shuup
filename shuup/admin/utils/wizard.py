# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings

from shuup import configuration
from shuup.admin.module_registry import get_modules
from shuup.core.models import Shop
from shuup.utils.importing import load


def load_setup_wizard_panes(shop, request=None, visible_only=True):
    panes = []
    for pane_spec in getattr(settings, "SHUUP_SETUP_WIZARD_PANE_SPEC", []):
        pane_class = load(pane_spec)
        pane_inst = pane_class(request=request, object=shop)
        if not visible_only or pane_inst.visible():
            panes.append(pane_inst)
    return panes


def setup_wizard_complete():
    """
    Check if shop wizard should be run.

    :return: whether setup wizard needs to be run
    :rtype: boolean
    """
    if getattr(settings, "SHUUP_ENABLE_MULTIPLE_SHOPS", False):
        # setup wizard is only applicable in single shop mode
        return True
    shop = Shop.objects.first()
    complete = configuration.get(shop, "setup_wizard_complete")
    if complete is None:
        return not setup_wizard_visible_panes(shop)
    return complete


def setup_wizard_visible_panes(shop):
    """
    Check if shop wizard has visible panes that require merchant configuration.

    :return: whether the setup wizard has visible panes
    :rtype: Boolean
    """
    return len(load_setup_wizard_panes(shop)) > 0


def setup_blocks_complete(request):
    """
    Check if any incomplete setup blocks remain.

    :return: whether all setup blocks are complete
    :rtype: Boolean
    """
    for module in get_modules():
        if len([block for block in module.get_help_blocks(request=request, kind="setup") if not block.done]) > 0:
            return False
    return True


def onboarding_complete(request):
    """
    Check if the shop wizard and all setup blocks are complete

    :return: whether onboarding is complete
    :rtype: Boolean
    """
    return setup_wizard_complete() and setup_blocks_complete(request)
