# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from optparse import make_option

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import translation

from shoop.testing.mock_population import Populator


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--with-superuser", default=None),
    )

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGES[0][0])
        superuser_name = options.get("with_superuser")
        if superuser_name:
            user = get_user_model().objects.filter(username=superuser_name).first()
            if not user:
                user = get_user_model().objects.create_superuser(
                    username=superuser_name,
                    email="%s@shoop.local" % superuser_name,
                    password=superuser_name,
                )
                print("Superuser created: %s" % user)
            else:
                print("Superuser pre-existed: %s" % user)
        Populator().populate()
