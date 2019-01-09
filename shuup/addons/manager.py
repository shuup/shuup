# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import codecs
import os

from pkg_resources import WorkingSet


def get_addons_from_entry_points():
    # TODO: Document me
    addons = set()

    # Use `pkg_resources.WorkingSet().iter_entry_points()` instead of
    # `pkg_resources.iter_entry_points()` to ensure we get a fresh list
    # regardless of whether the current cached working set has changed.
    # (The working set will change if addons are installed.)

    for entry_point in WorkingSet().iter_entry_points(group='shuup.addon'):
        addons.add(entry_point.name)
    return addons


def get_enabled_addons(file_path):
    # TODO: Document me
    available_addons = get_addons_from_entry_points()
    enabled_addons = []

    if os.path.isfile(file_path):
        with codecs.open(file_path, "r", "utf-8", errors="replace") as f:
            enabled_addons = f.read().splitlines()

    return [addon for addon in enabled_addons if addon in available_addons]


def set_enabled_addons(file_path, addons, comment=None):
    with codecs.open(file_path, "w", "utf-8") as f:
        if comment:
            f.write("# %s\n\n" % comment)
        for addon in addons:
            f.write("%s\n" % addon)


def add_enabled_addons(addon_filename, apps):
    # TODO: Document me
    iter_type = type(apps)
    return iter_type(list(apps) + get_enabled_addons(addon_filename))
