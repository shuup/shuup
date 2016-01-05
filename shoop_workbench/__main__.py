#!/usr/bin/env python
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.realpath(os.path.dirname(__file__) + "/.."))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shoop_workbench.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
