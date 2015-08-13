# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from easy_thumbnails.files import get_thumbnailer
from enumfields import Enum, EnumIntegerField
from filer.fields.file import FilerFileField
from parler.models import TranslatableModel, TranslatedFields

from shoop.core.fields import InternalIdentifierField


class ProductMediaKind(Enum):
    GENERIC_FILE = 1
    IMAGE = 2
    DOCUMENTATION = 3
    SAMPLE = 4

    class Labels:
        GENERIC_FILE = _('file')
        IMAGE = _('image')
        DOCUMENTATION = _('documentation')
        SAMPLE = _('sample')


@python_2_unicode_compatible
class ProductMedia(TranslatableModel):
    identifier = InternalIdentifierField(unique=True)
    product = models.ForeignKey("Product", related_name="media")
    shops = models.ManyToManyField("Shop", related_name="product_media")
    kind = EnumIntegerField(
        ProductMediaKind, db_index=True, default=ProductMediaKind.GENERIC_FILE, verbose_name=_('kind')
    )
    file = FilerFileField(blank=True, null=True, verbose_name=_('file'))
    external_url = models.URLField(blank=True, null=True, verbose_name=u'URL')
    ordering = models.IntegerField(default=0)

    # Status
    enabled = models.BooleanField(db_index=True, default=True, verbose_name=_("enabled"))
    public = models.BooleanField(default=True, blank=True, verbose_name=_('public (shown on product page)'))
    purchased = models.BooleanField(
        default=False, blank=True, verbose_name=_('purchased (shown for finished purchases)')
    )

    translations = TranslatedFields(
        title=models.CharField(blank=True, max_length=128, verbose_name=_('title')),
        description=models.TextField(blank=True, verbose_name=_('description')),
    )

    class Meta:
        verbose_name = _('product attachment')
        verbose_name_plural = _('product attachments')
        ordering = ["ordering", ]

    def __str__(self):  # pragma: no cover
        return self.effective_title

    @property
    def effective_title(self):
        title = self.safe_translation_getter("title")
        if title:
            return title

        if self.file_id:
            return self.file.label

        if self.external_url:
            return self.external_url

        return _('attachment')

    @property
    def url(self):
        if not self.public:
            raise ValueError("`get_effective_url()` may not be used on non-public media")

        if self.file_id:
            return self.file.url
        else:
            return self.external_url

    @property
    def easy_thumbnails_thumbnailer(self):
        if self.file_id:
            return get_thumbnailer(self.file)
