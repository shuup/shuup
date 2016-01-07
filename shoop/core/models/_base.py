# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import parler.models
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import force_text, python_2_unicode_compatible
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
        return force_text(name)  # ensure no lazy objects are returned

    class Meta:
        abstract = True


class ChangeProtected(object):
    protected_fields = None
    unprotected_fields = []
    change_protect_message = _("The following fields can not be changed")

    def clean(self, *args, **kwargs):
        super(ChangeProtected, self).clean(*args, **kwargs)
        if self.pk:
            changed_protected_fields = self._get_changed_protected_fields()
            if changed_protected_fields and self._are_changes_protected():
                message = "{change_protect_message}: {fields}".format(
                    change_protect_message=self.change_protect_message,
                    fields=", ".join(sorted(changed_protected_fields)),
                )
                raise ValidationError(message)

    def save(self, *args, **kwargs):
        self.clean()
        super(ChangeProtected, self).save(*args, **kwargs)

    def _are_changes_protected(self):
        """
        Check if changes of this object should be protected.

        This can be overridden in the subclasses to make it possible to
        avoid change protection e.g. if object is not in use yet.

        The base class implementation just returns True.
        """
        return True

    def _get_changed_protected_fields(self):
        if self.protected_fields is not None:
            protected_fields = self.protected_fields
        else:
            protected_fields = [
                x.name for x in self._meta.get_fields()
                if not x.is_relation and x.name not in self.unprotected_fields]
        in_db = type(self).objects.get(pk=self.pk)
        return [
            field for field in protected_fields
            if getattr(self, field) != getattr(in_db, field)]
