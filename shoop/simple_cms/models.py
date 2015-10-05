# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import markdown
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields

from shoop.core.fields import InternalIdentifierField


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
class Page(TranslatableModel):
    available_from = models.DateTimeField(null=True, blank=True)
    available_to = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="+", on_delete=models.SET_NULL)
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="+", on_delete=models.SET_NULL)

    created_on = models.DateTimeField(auto_now_add=True, editable=False)
    modified_on = models.DateTimeField(auto_now=True, editable=False)

    identifier = InternalIdentifierField(
        unique=True,
        help_text=_('This identifier can be used in templates to create URLs'),
        editable=True
    )

    visible_in_menu = models.BooleanField(_("Visible in menu"), default=False)

    translations = TranslatedFields(
        title=models.CharField(max_length=256, verbose_name=_('Page Title')),
        url=models.CharField(
            max_length=100, verbose_name=_('Page URL'),
            unique=True,
            default=None,
            blank=True,
            null=True
        ),
        content=models.TextField(verbose_name=_('Content')),
    )

    objects = PageQuerySet.as_manager()

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
        return markdown.markdown(self.content)

    def __str__(self):
        return force_text(self.safe_translation_getter("title", any_language=True, default=_("Untitled")))
