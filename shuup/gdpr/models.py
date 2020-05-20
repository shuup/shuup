# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import activate, get_language
from parler.models import TranslatableModel, TranslatedFields
from reversion.models import Version

from shuup.gdpr.utils import get_active_consent_pages
from shuup.simple_cms.models import Page

GDPR_ANONYMIZE_TASK_TYPE_IDENTIFIER = "gdpr_anonymize"


@python_2_unicode_compatible
class GDPRSettings(TranslatableModel):
    shop = models.OneToOneField("shuup.Shop", related_name="gdpr_settings")
    enabled = models.BooleanField(
        default=False,
        verbose_name=_('enabled'),
        help_text=_("Define if the GDPR is active.")
    )
    skip_consent_on_auth = models.BooleanField(
        default=False,
        verbose_name=_("skip consent on login"),
        help_text=_("Do not require consent on login when GDPR is activated.")
    )
    privacy_policy_page = models.ForeignKey(
        "shuup_simple_cms.Page",
        null=True,
        verbose_name=_("privacy policy page"),
        help_text=_("Choose your privacy policy page here. If this page changes, customers will be "
                    "prompted for new consent."))
    consent_pages = models.ManyToManyField(
        "shuup_simple_cms.Page",
        verbose_name=_("consent pages"),
        related_name="consent_settings",
        help_text=_("Choose pages here which are being monitored for customer consent. If any of these pages change, "
                    "the customer is being prompted for a new consent."))
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
        ),
        auth_consent_text=models.TextField(
            blank=True,
            verbose_name=_("login consent text"),
            help_text=_("Shown in login page between the form and the button. "
                        "Optional, but should be considered when the consent on login is disabled.")
        )
    )

    class Meta:
        verbose_name = _('GDPR settings')
        verbose_name_plural = _('GDPR settings')

    def __str__(self):
        return _("GDPR for {}").format(self.shop)

    def set_default_content(self):
        language = get_language()
        for code, name in settings.LANGUAGES:
            activate(code)
            self.set_current_language(code)
            self.cookie_banner_content = settings.SHUUP_GDPR_DEFAULT_BANNER_STRING
            self.cookie_privacy_excerpt = settings.SHUUP_GDPR_DEFAULT_EXCERPT_STRING
            self.save()

        self.set_current_language(language)
        activate(language)

    @classmethod
    def get_for_shop(cls, shop):
        instance, created = cls.objects.get_or_create(shop=shop)
        if created or not instance.safe_translation_getter("cookie_banner_content"):
            instance.set_default_content()
        return instance


@python_2_unicode_compatible
class GDPRCookieCategory(TranslatableModel):
    shop = models.ForeignKey("shuup.Shop", related_name="gdpr_cookie_categories")
    always_active = models.BooleanField(default=False, verbose_name=_('always active'))
    default_active = models.BooleanField(
        verbose_name=_('active by default'),
        default=False,
        help_text=_('whether this cookie category is active by default')
    )
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
        verbose_name = _('GDPR cookie category')
        verbose_name_plural = _('GDPR cookie categories')

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
        "GDPRUserConsentDocument",
        verbose_name=_("consent documents"),
        blank=True,
        editable=False
    )

    class Meta:
        verbose_name = _('GDPR user consent')
        verbose_name_plural = _('GDPR user consents')

    @classmethod
    def ensure_for_user(cls, user, shop, consent_documents):
        documents = []
        for page in consent_documents:
            Page.create_initial_revision(page)
            version = Version.objects.get_for_object(page).first()
            consent_document = GDPRUserConsentDocument.objects.create(
                page=page,
                version=version
            )
            documents.append(consent_document)

        # ensure only one consent exists for this user in this shop
        consent = cls.objects.filter(shop=shop, user=user).first()
        if consent:
            consents = cls.objects.filter(shop=shop, user=user).order_by("-created_on")
            if consents.count() > 1:
                # There are multiple consents, remove excess
                ids = [c.id for c in consents.all() if c.id != consent.id]
                cls.objects.filter(pk__in=ids).delete()
        else:
            consent = cls.objects.create(shop=shop, user=user)

        consent.documents = documents
        return consent

    @classmethod
    def get_for_user(cls, user, shop):
        return cls.objects.filter(user=user, shop=shop).order_by("-created_on").first()

    def should_reconsent(self, shop, user):
        consent_pages_ids = set([page.id for page in get_active_consent_pages(shop)])
        page_ids = set([doc.page.id for doc in self.documents.all()])
        if consent_pages_ids != page_ids:
            return True

        # all matches, check versions
        for consent_document in self.documents.all():
            version = Version.objects.get_for_object(consent_document.page).first()
            if consent_document.version != version:
                return True

        return False

    def should_reconsent_to_page(self, page):
        version = Version.objects.get_for_object(page).first()
        return not self.documents.filter(page=page, version=version).exists()

    def __str__(self):
        return _("GDPR user consent in {} for user {} in shop {}").format(self.created_on, self.user, self.shop)


@python_2_unicode_compatible
class GDPRUserConsentDocument(models.Model):
    page = models.ForeignKey("shuup_simple_cms.Page")
    version = models.ForeignKey(Version)

    def __str__(self):
        return _("GDPR user consent document for {} (Version: {})").format(self.page, self.version)
