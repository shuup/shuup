# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields


@python_2_unicode_compatible
class GDPRSettings(TranslatableModel):
    shop = models.OneToOneField("shuup.Shop", related_name="gdpr_settings")
    enabled = models.BooleanField(
        default=False,
        verbose_name=_('enabled'),
        help_text=_("Define if the GDPR is active.")
    )
    translations = TranslatedFields(
        cookie_banner_content=models.TextField(
            blank=True,
            verbose_name=_("cookie banner content"),
            help_text=_("The text to be present to users in cookie pop-up warning.")
        ),
        cookie_privacy_excerpt=models.TextField(
            blank=True,
            verbose_name=_("cookie privacy excerpt"),
            help_text=_("The summary text to be present about cookie privacy.")
        )
    )

    class Meta:
        verbose_name = _('gdpr settings')
        verbose_name_plural = _('gdpr settings')

    def __str__(self):
        return _("GDPR for {}").format(self.shop)

    @classmethod
    def get_for_shop(cls, shop):
        return cls.objects.get_or_create(shop=shop)[0]


@python_2_unicode_compatible
class GDPRCookieCategory(TranslatableModel):
    shop = models.ForeignKey("shuup.Shop", related_name="hdpr_cookie_categories")
    always_active = models.BooleanField(default=False, verbose_name=_('always active'))
    cookies = models.TextField(
        verbose_name=_("cookies used"),
        help_text=_(
            "Comma separated list of cookies names, prefix or sufix "
            "that will be included in this category, "
            "e.g. _ga, mysession, user_c_"
        ),
    )
    translations = TranslatedFields(
        name=models.CharField(max_length=64, verbose_name=_("name")),
        how_is_used=models.TextField(
            verbose_name=_("how we use"),
            help_text=_("Describe the purpose of this category of cookies and how it is used."),
            blank=True
        )
    )

    class Meta:
        verbose_name = _('gdpr cookie category')
        verbose_name_plural = _('gdpr cookie categories')

    def __str__(self):
        return _("GDPR cookie category for {}").format(self.shop)
