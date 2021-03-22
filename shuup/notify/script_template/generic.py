# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.widgets import TextEditorWidget
from shuup.notify.actions import SendEmail
from shuup.notify.script import Step, StepNext
from shuup.notify.script_template import BaseScriptTemplate
from shuup.utils.form_group import FormGroup


class GenericScriptTemplateEmailContentForm(forms.Form):
    """
    Generic form which contains the content of a email: subject and body.
    """

    subject = forms.CharField(label=_("Subject"), help_text=_("The subject of the email"))
    body = forms.CharField(label=_("Email content"), widget=TextEditorWidget, help_text=_("The content of the email."))


class GenericScriptTemplateEmailForm(forms.Form):
    """
    Generic form which contains a destination of the email.
    """

    SEND_TO_CHOICES = [
        ("customer", _("Customer")),
        ("other", _("Other destination")),
    ]
    send_to = forms.ChoiceField(
        label=_("Send to?"),
        initial="customer",
        choices=SEND_TO_CHOICES,
        widget=forms.Select(attrs={"class": "no-select2"}),
        help_text=_("You can send this email to the customer or to " "other email of your choice."),
    )
    recipient = forms.EmailField(
        label=_("Destination"), required=False, help_text=_("Fill with the destination email address.")
    )

    def clean(self):
        cleaned_data = super(GenericScriptTemplateEmailForm, self).clean()
        send_to = cleaned_data.get("send_to")
        recipient = cleaned_data.get("recipient")

        if send_to == "other" and not recipient:
            self.add_error(
                "recipient", _("Recipient is a required field when you don't want to " "send the email to customer.")
            )
        return cleaned_data


class GenericSendEmailScriptTemplate(BaseScriptTemplate):
    """
    A generic ScriptTemplate which needs email configurations such as recipient, subject and body.

    This class also deals with a multi-language form to receive translated email's subject and body.

    The form of this ScriptTemplate is a `FormGroup` which will contain a `base` form which has no translation
    and also intances of `multilingual_form_class`, one for each available LANGUAGE. Only the form for the
    default language (provided by `PARLER_DEFAULT_LANGUAGE_CODE` setting) is required.

    :ivar: django.form.Form base_form_class: the main form, not included in the group of translation fields.
    :ivar: django.form.Form multilingual_form_class: the form which will be created for each available language.
    """

    template_name = "notify/admin/generic_script_template.jinja"
    extra_js_template_name = "notify/admin/generic_script_template_extra_js.jinja"
    base_form_class = GenericScriptTemplateEmailForm
    multilingual_form_class = GenericScriptTemplateEmailContentForm

    def get_script_steps(self, form):
        action_data = {
            "template_data": {},
            "language": {"constant": settings.PARLER_DEFAULT_LANGUAGE_CODE},
        }

        if form["base"].cleaned_data.get("send_to") == "other":
            action_data["recipient"] = {"constant": form["base"].cleaned_data["recipient"]}
        else:
            action_data["recipient"] = {"variable": "customer_email"}

        for language in form.forms:
            form_lang = form[language]
            # tries to get the cleaned data, otherwise the initial value
            # since cleaned_data will be blank if the user did not change anything
            action_data["template_data"][language] = {
                "content_type": "html",
                "subject": form_lang.cleaned_data.get("subject", form_lang.initial.get("subject", "")).strip(),
                "body": form_lang.cleaned_data.get("body", form_lang.initial.get("body", "")).strip(),
            }

        send_mail_action = SendEmail(action_data)
        return [Step(next=StepNext.STOP, actions=(send_mail_action,))]

    def get_context_data(self):
        context = super(GenericSendEmailScriptTemplate, self).get_context_data()
        context["languages"] = dict(settings.LANGUAGES)
        context["default_language"] = settings.PARLER_DEFAULT_LANGUAGE_CODE
        return context

    def get_form(self, **kwargs):
        """
        Create a `FormGroup` and put the necessary forms inside.
        """
        kwargs.update(self.get_form_kwargs())
        form_group = FormGroup(**kwargs)
        form_group.add_form_def("base", self.base_form_class, required=True)
        default_language = settings.PARLER_DEFAULT_LANGUAGE_CODE

        # the first form must be the first form, and required, as it is the fallback
        form_group.add_form_def(default_language, self.multilingual_form_class, required=True)

        for language, __ in settings.LANGUAGES:
            # the default language was already added!
            if language == default_language:
                continue
            form_group.add_form_def(language, self.multilingual_form_class, required=False)

        return form_group

    def get_initial(self):
        # if we have a script bound, parse its content
        if self.script_instance:
            send_email = None

            # search for the SendEmail action
            for step in self.script_instance.get_steps():
                for action in step._actions:
                    if isinstance(action, SendEmail):
                        send_email = action
                        break

            send_to_customer = send_email.data.get("recipient", {}).get("variable") == "customer_email"
            recipient = "" if send_to_customer else send_email.data["recipient"].get("constant", "")

            initial = {"base-recipient": recipient, "base-send_to": "customer" if send_to_customer else "other"}

            for language, data in send_email.data["template_data"].items():
                for data_key, data_value in data.items():
                    initial["{0}-{1}".format(language, data_key)] = data_value
            return initial

        else:
            return super(GenericSendEmailScriptTemplate, self).get_initial()

    def can_edit_script(self):
        """
        We can only edit the script when:
            * the event is what we expect
            * has a single SendMail action in steps (oterwise we don't know which to edit)
        """
        if self.script_instance.event_identifier != self.event.identifier:
            return False

        send_mails = []
        for step in self.script_instance.get_steps():
            send_mails.extend(list(filter(lambda action: isinstance(action, SendEmail), step._actions)))
        return len(send_mails) == 1
