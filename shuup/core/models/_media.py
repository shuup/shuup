# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from filer.fields.file import FilerFileField
from filer.fields.folder import FilerFolderField


@python_2_unicode_compatible
class MediaFile(models.Model):
    file = FilerFileField(related_name="media_file", verbose_name=_("file"), on_delete=models.CASCADE)
    shops = models.ManyToManyField(
        "shuup.Shop", related_name="media_files", verbose_name=_('shops'),
        help_text=_("Select which shops you would like the files to be visible in."))

    def __str__(self):  # pragma: no cover
        return "%s" % (self.file)


@python_2_unicode_compatible
class MediaFolder(models.Model):
    folder = FilerFolderField(related_name="media_folder", verbose_name=_("folder"), on_delete=models.CASCADE)
    shops = models.ManyToManyField(
        "shuup.Shop", related_name="media_folders", verbose_name=_('shops'),
        help_text=_("Select which shops you would like the folder to be visible in.")
    )

    visible = models.BooleanField(
        default=False, verbose_name=_("visible"),
        help_text=_("Should this folder be visible for everyone in the media browser")
    )

    owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name=_("owning_media_folders"), verbose_name=_('owners'),
        help_text=_("Select which users will own this folder.")
    )

    def __str__(self):  # pragma: no cover
        return "%s" % (self.folder)

    def get_all_children(self):
        folders = [self.folder]
        for sub_folder in self.folder.children.all():
            for sub_media_folder in sub_folder.media_folder.all():
                folders.extend(sub_media_folder.get_all_children())
        return folders
