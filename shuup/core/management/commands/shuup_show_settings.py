# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
Show known Shuup settings and their values.
"""
from optparse import make_option

from django.core.management.base import BaseCommand

import shuup.utils.settings_doc


class Command(BaseCommand):
    help = __doc__.strip()

    option_list = BaseCommand.option_list + (
        make_option(
            '--only-changed', action='store_true', default=False,
            help='Show only settings with non-default values'),
    )

    def handle(self, *args, **options):
        docs = shuup.utils.settings_doc.get_known_settings_documentation(
            only_changed=options['only_changed'])
        self.stdout.write(docs)
