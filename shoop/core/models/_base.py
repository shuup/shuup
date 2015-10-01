# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import parler.models
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from shoop.utils import text


class ShoopModel(models.Model):
    """
    Shoop Model.
    """
    identifier_attr = 'identifier'

    def __repr__(self):
        if hasattr(self, self.identifier_attr):
            identifier = getattr(self, self.identifier_attr) or ''
            identifier_suf = '-{}'.format(text.force_ascii(identifier))
        else:
            identifier_suf = ''
        return '<{}:{}{}>'.format(type(self).__name__, self.pk, identifier_suf)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class TranslatableShoopModel(ShoopModel, parler.models.TranslatableModel):
    name_attr = 'name'

    def __str__(self):
        name = self.safe_translation_getter(self.name_attr, any_language=True)
        if name is None:
            return '{}:{}'.format(type(self).__name__, self.pk)
        return name

    class Meta:
        abstract = True


class ImmutableMixin(object):
    unprotected_fields = []
    immutability_message = _("Cannot change immutable object that is in use")

    def clean(self, *args, **kwargs):
        super(ImmutableMixin, self).clean(*args, **kwargs)
        if self.pk:
            if self._has_any_protected_field_changed() and self._is_in_use():
                raise ValidationError(self.immutability_message)

    def save(self, *args, **kwargs):
        self.clean()
        super(ImmutableMixin, self).save(*args, **kwargs)

    def _is_in_use(self):
        return True

    def _has_any_protected_field_changed(self):
        protected_fields = [
            x.name for x in self._meta.get_fields()
            if not x.is_relation and x.name not in self.unprotected_fields]
        in_db = type(self).objects.get(pk=self.pk)
        return any(
            getattr(self, field) != getattr(in_db, field)
            for field in protected_fields)
