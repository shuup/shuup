# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields

from shuup.core.fields import InternalIdentifierField


class PageQuerySet(TranslatableQuerySet):
    def visible(self, dt=None):
        """
        Get pages that should be publicly visible.

        This does not do permission checking.

        :param dt: Datetime for visibility check
        :type dt: datetime.datetime
        :return: QuerySet of pages.
        :rtype: QuerySet[Page]
        """
        if not dt:
            dt = now()
        q = Q(available_from__lte=dt) & (Q(available_to__gte=dt) | Q(available_to__isnull=True))
        qs = self.filter(q)
        return qs


@python_2_unicode_compatible
class Page(MPTTModel, TranslatableModel):
    available_from = models.DateTimeField(null=True, blank=True, verbose_name=_('available from'), help_text=_(
        "Set an available from date to restrict the page to be available only after a certain date and time. "
        "This is useful for pages describing sales campaigns or other time-sensitive pages."
    ))
    available_to = models.DateTimeField(null=True, blank=True, verbose_name=_('available to'), help_text=_(
        "Set an available to date to restrict the page to be available only after a certain date and time. "
        "This is useful for pages describing sales campaigns or other time-sensitive pages."
    ))

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="+", on_delete=models.SET_NULL,
        verbose_name=_('created by')
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="+", on_delete=models.SET_NULL,
        verbose_name=_('modified by')
    )

    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('created on'))
    modified_on = models.DateTimeField(auto_now=True, editable=False, verbose_name=_('modified on'))

    identifier = InternalIdentifierField(
        unique=True,
        help_text=_('This identifier can be used in templates to create URLs'),
        editable=True
    )

    visible_in_menu = models.BooleanField(verbose_name=_("visible in menu"), default=False, help_text=_(
        "Check this if this page should have a link in the top menu of the store front."
    ))
    parent = TreeForeignKey(
        "self", blank=True, null=True, related_name="children", verbose_name=_("parent"), help_text=_(
            "Set this to a parent page if this page should be subcategorized under another page."
        ))
    list_children_on_page = models.BooleanField(verbose_name=_("list children on page"), default=False, help_text=_(
        "Check this if this page should list its children pages."
    ))

    translations = TranslatedFields(
        title=models.CharField(max_length=256, verbose_name=_('title'), help_text=_(
            "The page title. This is shown anywhere links to your page are shown."
        )),
        url=models.CharField(
            max_length=100, verbose_name=_('URL'),
            unique=True,
            default=None,
            blank=True,
            null=True,
            help_text=_(
                "The page url. Choose a descriptive url so that search engines can rank your page higher. "
                "Often the best url is simply the page title with spaces replaced with dashes."
            )
        ),
        content=models.TextField(verbose_name=_('content'), help_text=_(
            "The page content. This is the text that is displayed when customers click on your page link."
        )),
    )

    objects = TreeManager.from_queryset(PageQuerySet)()

    class Meta:
        ordering = ('-id',)
        verbose_name = _('page')
        verbose_name_plural = _('pages')

    def is_visible(self, dt=None):
        if not dt:
            dt = now()

        return (
            (self.available_from and self.available_from <= dt) and
            (self.available_to is None or self.available_to >= dt)
        )

    def get_html(self):
        return self.content

    def __str__(self):
        return force_text(self.safe_translation_getter("title", any_language=True, default=_("Untitled")))
