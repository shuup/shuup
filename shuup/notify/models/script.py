# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from jsonfield.fields import JSONField

from shuup.core.fields import InternalIdentifierField
from shuup.notify.base import Event
from shuup.notify.enums import StepNext
from shuup.utils.analog import define_log_model


@python_2_unicode_compatible
class Script(models.Model):
    shop = models.ForeignKey("shuup.Shop", verbose_name=_("shop"))
    event_identifier = models.CharField(max_length=64, blank=False, db_index=True, verbose_name=_('event identifier'))
    identifier = InternalIdentifierField(unique=True)
    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('created on'))
    name = models.CharField(max_length=64, verbose_name=_('name'))
    enabled = models.BooleanField(default=False, db_index=True, verbose_name=_('enabled'))
    _step_data = JSONField(default=[], db_column="step_data")
    template = models.CharField(
        max_length=64, blank=True, null=True,
        default=None, verbose_name=_('template identifier'),
        help_text=_('the template identifier used to create this script')
    )

    def get_steps(self):
        """
        :rtype Iterable[Step]
        """
        if getattr(self, "_steps", None) is None:
            from shuup.notify.script import Step
            self._steps = [Step.unserialize(data) for data in self._step_data]
        return self._steps

    def set_steps(self, steps):
        self._step_data = [step.serialize() for step in steps]
        self._steps = steps

    def get_serialized_steps(self):
        return [step.serialize() for step in self.get_steps()]

    def set_serialized_steps(self, serialized_data):
        self._steps = None
        self._step_data = serialized_data
        # Poor man's validation
        for step in self.get_steps():
            pass

    @property
    def event_class(self):
        return Event.class_for_identifier(self.event_identifier)

    def __str__(self):
        return self.name

    def execute(self, context):
        """
        Execute the script in the given context.

        :param context: Script context
        :type context: shuup.notify.script.Context
        """
        for step in self.get_steps():
            if step.execute(context) == StepNext.STOP:
                break


ScriptLogEntry = define_log_model(Script)
