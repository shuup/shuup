# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
"""
Extract translatable strings from shoop
"""
from __future__ import unicode_literals

import logging
import subprocess

import os
from django.conf import settings
from django.core import management
from django.core.management import BaseCommand


logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    def handle(self, *args, **options):
        base_dir = os.path.join(settings.BASE_DIR, "..")
        os.chdir(base_dir)
        subprocess.check_call(["pybabel", "extract", "shoop", "-o" "shoop/locale/django.pot", "-F", "shoop/babel.cfg"])
        subprocess.check_call([
            "pybabel",
            "update",
            "-D", "django",
            "-i", "shoop/locale/django.pot",
            "-d", "shoop/locale",
            "-l", "en",
            "--ignore-obsolete"])

        base_dir = os.path.join(settings.BASE_DIR, "../shoop")
        os.chdir(base_dir)
        logging.info("Running makemessages for .js files")
        management.call_command("makemessages",
                                domain="djangojs",
                                locale=["en"],
                                ignore=["node_modules", "bower_components", "doc"])
