# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from easy_thumbnails.exceptions import InvalidImageFormatError
from easy_thumbnails.files import get_thumbnailer
from enumfields import Enum, EnumIntegerField
from filer.fields.file import FilerFileField
from parler.models import TranslatableModel, TranslatedFields

from shuup.core.fields import InternalIdentifierField
from shuup.utils.analog import define_log_model


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
    product = models.ForeignKey("Product", related_name="media", on_delete=models.CASCADE, verbose_name=_('product'))
    shops = models.ManyToManyField("Shop", related_name="product_media", verbose_name=_('shops'), help_text=_(
            "Select which shops you would like the product media to be visible in."
        )
    )
    kind = EnumIntegerField(
        ProductMediaKind, db_index=True, default=ProductMediaKind.GENERIC_FILE, verbose_name=_('kind'), help_text=_(
            "Select what type the media is. It can either be a normal file, part of the documentation, or a sample."
        )
    )
    file = FilerFileField(blank=True, null=True, verbose_name=_('file'), on_delete=models.CASCADE)
    external_url = models.URLField(
        blank=True, null=True, verbose_name=_('URL'),
        help_text=_("Enter URL to external file. If this field is filled, the selected media doesn't apply.")
    )
    ordering = models.IntegerField(default=0, verbose_name=_('ordering'), help_text=_(
            "You enter the numerical order that your image will be displayed on your product page."
        )
    )

    # Status
    enabled = models.BooleanField(db_index=True, default=True, verbose_name=_("enabled"))
    public = models.BooleanField(
        default=True, blank=True, verbose_name=_('public (shown on product page)'), help_text=_(
            "Check this if you would like the image shown on your product page. Checked by default."
        )
    )
    purchased = models.BooleanField(
        default=False, blank=True, verbose_name=_('purchased (shown for finished purchases)'), help_text=_(
            "Select this if you would like the product media shown for completed purchases."
        )
    )

    translations = TranslatedFields(
        title=models.CharField(blank=True, max_length=128, verbose_name=_('title'), help_text=_(
                "Choose a title for your product media. This will help it be found in your store and on the web."
            )
        ),
        description=models.TextField(blank=True, verbose_name=_('description'), help_text=_(
                "Write a description for your product media. This will help it be found in your store and on the web."
            )
        ),
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
        if self.external_url:
            return self.external_url
        if self.file:
            return self.file.url
        return ""

    @property
    def easy_thumbnails_thumbnailer(self):
        """
        Get `Thumbnailer` instance.

        Will return `None` if file cannot be thumbnailed.

        :rtype:easy_thumbnails.files.Thumbnailer|None
        """
        if not self.file_id:
            return None

        if self.kind != ProductMediaKind.IMAGE:
            return None

        return get_thumbnailer(self.file)

    def get_thumbnail(self, **kwargs):
        """
        Get thumbnail for image

        This will return `None` if there is no file or kind is not `ProductMediaKind.IMAGE`

        :rtype: easy_thumbnails.files.ThumbnailFile|None
        """
        kwargs.setdefault("size", (64, 64))
        kwargs.setdefault("crop", True)  # sane defaults
        kwargs.setdefault("upscale", True)  # sane defaults

        if kwargs["size"] is (0, 0):
            return None

        thumbnailer = self.easy_thumbnails_thumbnailer

        if not thumbnailer:
            return None

        try:
            return thumbnailer.get_thumbnail(thumbnail_options=kwargs)
        except InvalidImageFormatError:
            return None


ProductMediaLogEntry = define_log_model(ProductMedia)
