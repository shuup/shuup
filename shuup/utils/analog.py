# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from jsonfield import JSONField

from shuup.utils.django_compat import force_text


class LogEntryKind(Enum):
    OTHER = 0
    AUDIT = 1
    EDIT = 2
    DELETION = 3
    NOTE = 4
    EMAIL = 5
    WARNING = 6
    ERROR = 7

    class Labels:
        OTHER = _("other")
        AUDIT = _("audit")
        EDIT = _("edit")
        DELETION = _("deletion")
        NOTE = _("note")
        EMAIL = _("email")
        WARNING = _("warning")
        ERROR = _("error")


class BaseLogEntry(models.Model):
    target = None  # This will be overridden dynamically
    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_("created on"))
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, verbose_name=_("user"))
    message = models.CharField(max_length=1024, verbose_name=_("message"))
    identifier = models.CharField(max_length=256, db_index=True, blank=True, verbose_name=_("identifier"))
    kind = EnumIntegerField(LogEntryKind, default=LogEntryKind.OTHER, verbose_name=_("log entry kind"))
    extra = JSONField(null=True, blank=True, verbose_name=_("extra data"))

    class Meta:
        abstract = True


all_known_log_models = {}


def define_log_model(model_class):
    log_model_name = "%sLogEntry" % model_class.__name__

    class Meta:
        app_label = model_class._meta.app_label
        abstract = False

    class_dict = {
        "target": models.ForeignKey(
            model_class, related_name="log_entries", on_delete=models.CASCADE, verbose_name=_("target")
        ),
        "__module__": model_class.__module__,
        "Meta": Meta,
        "logged_model": model_class,
    }

    log_entry_class = type(str(log_model_name), (BaseLogEntry,), class_dict)

    def _add_log_entry(self, message, identifier=None, kind=LogEntryKind.OTHER, user=None, extra=None, save=True):
        # You can also pass something that contains "user" as an
        # attribute for an user
        user = getattr(user, "user", user) or None
        if not getattr(user, "pk", None):
            user = None
        log_entry = log_entry_class(
            target=self,
            message=force_text(message or "", errors="ignore")[:1024],
            identifier=force_text(identifier or "", errors="ignore")[:256],
            user=user,
            kind=kind,
            extra=(extra or None),
        )
        if save:
            log_entry.save()
        return log_entry

    setattr(model_class, "add_log_entry", _add_log_entry)
    all_known_log_models[model_class] = log_entry_class
    return log_entry_class
