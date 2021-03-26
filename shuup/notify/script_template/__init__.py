# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup.notify.base import ScriptTemplate
from shuup.notify.models.script import Script


class BaseScriptTemplate(ScriptTemplate):
    """
    A base ScriptTemplate class which provides implementation for create and update the script.
    """

    def get_script_steps(self, form=None):
        """
        Returns a list of Steps to use in the script.

        :param django.forms.Form|None form: validated form to use or None

        :return: list of steps
        :rtype: list[shuup.notify.Step]
        """
        return []

    def create_script(self, shop, form=None):
        """ Creates the script based on the event and the steps """
        script = Script(event_identifier=self.event.identifier, name=self.name, enabled=True, shop=shop)
        script.set_steps(self.get_script_steps(form))
        script.save()
        return script

    def update_script(self, form):
        """ Change the steps and save the script """
        self.script_instance.set_steps(self.get_script_steps(form))
        self.script_instance.save()
        return self.script_instance
