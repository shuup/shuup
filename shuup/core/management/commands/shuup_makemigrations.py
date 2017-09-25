# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.management.commands.makemigrations import Command  # noqa
from django.db import models

original_deconstruct = models.Field.deconstruct


def new_deconstruct(self):
    name, path, args, kwargs = original_deconstruct(self)
    if 'help_text' in kwargs:
        del kwargs['help_text']
    if 'verbose_name' in kwargs:
        del kwargs['verbose_name']
    return name, path, args, kwargs


models.Field.deconstruct = new_deconstruct
