# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.template.defaultfilters import linebreaksbr
from django.utils.translation import ugettext_lazy as _

from shuup.notify.actions import SendEmail
from shuup.notify.conditions import BooleanEqual
from shuup.notify.script import Step, StepNext
from shuup.notify.script_template.generic import GenericSendEmailScriptTemplate
from shuup.simple_supplier.notify_events import AlertLimitReached


class StockLimitEmailForm(forms.Form):
    recipient = forms.EmailField(label=_("Send to?"),
                                 help_text=_("Send email to whom?"))
    last24hrs = forms.BooleanField(label=_("Do not send the same email within 24 hours."),
                                   initial=True,
                                   required=False,
                                   help_text=_("If enabled, avoids sending the same email for the same "
                                               "product and supplier within 24 hours."))


class StockLimitEmailScriptTemplate(GenericSendEmailScriptTemplate):
    identifier = "stocks_limit_email"
    event = AlertLimitReached
    name = _("Send Stock Limit Alert Email")
    description = _("Send me an email when a product stock is lower than the configured limit.")
    help_text = _("This script will send an email to the configured destination alerting about the "
                  "a product's low stock of a supplier. You can configure to not send the same email "
                  "multiple times in a period of 24 hours. Every time a product's stock reach its configured limit, "
                  "this notification will be fired and the email sent.")
    extra_js_template_name = None       # remove the script from parent class
    base_form_class = StockLimitEmailForm

    def get_script_steps(self, form):
        action_data = {
            "template_data": {},
            "recipient": {"constant": form["base"].cleaned_data["recipient"]},
            "language": {"variable": "language"},
            "fallback_language": {"constant": settings.PARLER_DEFAULT_LANGUAGE_CODE}
        }

        for language in form.forms:
            form_lang = form[language]
            # tries to get the cleaned data, otherwise the initial value
            # since cleaned_data can be blank if the user did not change anything
            action_data["template_data"][language] = {
                "content_type": "html",
                "subject": form_lang.cleaned_data.get("subject", form_lang.initial.get("subject", "")).strip(),
                "body": form_lang.cleaned_data.get("body", form_lang.initial.get("body", "")).strip()
            }

        send_mail_action = SendEmail(action_data)
        conditions = []
        if form["base"].cleaned_data.get("last24hrs"):
            conditions.append(BooleanEqual({
                "v1": {"variable": "dispatched_last_24hs"},
                "v2": {"constant": (not form["base"].cleaned_data["last24hrs"])}
            }))

        return [Step(next=StepNext.STOP, actions=(send_mail_action,), conditions=conditions)]

    def get_initial(self):
        if self.script_instance:
            structure = self._find_expected_structure()
            if structure:
                condition = structure["condition"]
                last24hrs = (condition.data["v2"].get("constant", True) if condition else True)

                initial = {
                    "base-last24hrs": (not last24hrs),
                    "base-recipient": structure["send_mail"].data["recipient"].get("constant"),
                }

                for language, data in structure["send_mail"].data["template_data"].items():
                    for data_key, data_value in data.items():
                        initial["{0}-{1}".format(language, data_key)] = data_value
                return initial

        else:
            # only returns initial data for the default language
            default_lang = settings.PARLER_DEFAULT_LANGUAGE_CODE

            return {
                default_lang+"-subject": _("Low stock of: {{ product }} from {{ supplier }}"),
                default_lang+"-body": linebreaksbr(_("Hi!\n"
                                                     "You are receiving this message because the product "
                                                     "{{ product}} from {{ supplier }} has a low stock.")),
            }

    def _find_expected_structure(self):
        """
        Find and return the expected SendMail action and the BooleanEqual condition
        which matches the template requirements.

        :return: the found structure or None if it does not match with the expected one
        :rtype: dict|None
        """
        expected_send_mail = None
        expected_condition = None

        for step in self.script_instance.get_steps():
            for action in step._actions:
                if isinstance(action, SendEmail):
                    # we've found the action, but if we found another one just returns,
                    # because we have a unexpected structure
                    if expected_send_mail:
                        return
                    expected_send_mail = action

                # we check here, since the condition and the action must be in the same step
                if not expected_send_mail:
                    continue

                # maybe we don't find any condition since the user did not checked last24hrs checkbox
                for condition in step._conditions:
                    if not isinstance(condition, BooleanEqual):
                        continue

                    if (condition.data["v1"].get("variable") == "dispatched_last_24hs" and
                            "constant" in condition.data["v2"]):
                        # we've found the condition, but another one was found, leave
                        if expected_condition:
                            return
                        expected_condition = condition

                # all fine!
                return {
                    "send_mail": expected_send_mail,
                    "condition": expected_condition
                }

    def can_edit_script(self):
        """
        We can only edit the script when:
            * the event is AlertLimitReached
            * has a single SendMail action in steps (oterwise we don't know which to edit)
        """
        if self.script_instance.event_identifier != AlertLimitReached.identifier:
            return False

        structure = self._find_expected_structure()
        # we need a matching send mail action and a matching BooleanEqual condition
        if not structure:
            return False

        return True
