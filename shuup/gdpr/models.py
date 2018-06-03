# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields

GDPR_ANONYMIZE_TASK_TYPE_IDENTIFIER = "gdpr_anonymize"


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
            help_text=_("The text to be presented to users in a pop-up warning.")
        ),
        cookie_privacy_excerpt=models.TextField(
            blank=True,
            verbose_name=_("cookie privacy excerpt"),
            help_text=_("The summary text to be presented about cookie privacy.")
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
    shop = models.ForeignKey("shuup.Shop", related_name="gdpr_cookie_categories")
    always_active = models.BooleanField(default=False, verbose_name=_('always active'))
    cookies = models.TextField(
        verbose_name=_("cookies used"),
        help_text=_(
            "Comma separated list of cookies names, prefix or suffix "
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


@python_2_unicode_compatible
class GDPRUserConsent(models.Model):
    created_on = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        db_index=True,
        verbose_name=_("created on")
    )
    shop = models.ForeignKey(
        "shuup.Shop",
        related_name="gdpr_consents",
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='gdpr_consents',
        on_delete=models.PROTECT,
        editable=False
    )
    documents = models.ManyToManyField(
        "shuup_simple_cms.Page",
        verbose_name=_("consent documents"),
        blank=True,
        editable=False
    )

    class Meta:
        verbose_name = _('gdpr user consent')
        verbose_name_plural = _('gdpr user consents')

    @classmethod
    def create_for_user(cls, user, shop, consent_documents):
        gdpr_user_consent = cls.objects.create(shop=shop, user=user)
        gdpr_user_consent.documents = consent_documents
        return gdpr_user_consent

    def __str__(self):
        return _("GDPR user consent in {} for user {} in shop {}").format(self.created_on, self.user, self.shop)
