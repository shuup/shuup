# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
Show known Shuup settings and their values.
"""
from django.core.management.base import BaseCommand

import shuup.utils.settings_doc


class Command(BaseCommand):
    help = __doc__.strip()

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--only-changed", action="store_true", default=False, help="Show only settings with non-default values"
        )

    def handle(self, *args, **options):
        docs = shuup.utils.settings_doc.get_known_settings_documentation(only_changed=options["only_changed"])
        self.stdout.write(docs)
