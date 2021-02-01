# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import logging
from html import unescape

from django import forms
from django.conf import settings
from django.core.mail.message import EmailMessage
from django.utils.translation import ugettext as _

from shuup.admin.forms.widgets import CodeEditorWithHTMLPreview
from shuup.notify.base import Action, Binding
from shuup.notify.enums import ConstantUse, TemplateUse
from shuup.notify.models import EmailTemplate
from shuup.notify.signals import (
    notification_email_before_send, notification_email_sent
)
from shuup.notify.typology import Email, Language, Text


class SendEmail(Action):
    EMAIL_CONTENT_TYPE_CHOICES = (
        ('html', _('HTML')),
        ('plain', _('Plain text'))
    )

    identifier = "send_email"
    template_use = TemplateUse.MULTILINGUAL
    template_fields = {
        "subject": forms.CharField(required=True, label=_(u"Subject")),
        "email_template": forms.ChoiceField(
            choices=[(None, "-----")],
            label=_("Email Template"),
            required=False
        ),
        "body": forms.CharField(required=True, label=_("Email Body"), widget=CodeEditorWithHTMLPreview),
        "content_type": forms.ChoiceField(
            required=True, label=_(u"Content type"),
            choices=EMAIL_CONTENT_TYPE_CHOICES, initial=EMAIL_CONTENT_TYPE_CHOICES[0][0]
        )
    }
    recipient = Binding(_("Recipient"), type=Email, constant_use=ConstantUse.VARIABLE_OR_CONSTANT, required=True)
    reply_to_address = Binding(_("Reply-To"), type=Email, constant_use=ConstantUse.VARIABLE_OR_CONSTANT)
    cc = Binding(_("Carbon Copy (CC)"), type=Email, constant_use=ConstantUse.VARIABLE_OR_CONSTANT,)
    bcc = Binding(_("Blind Carbon Copy (BCC)"), type=Email, constant_use=ConstantUse.VARIABLE_OR_CONSTANT)
    from_email = Binding(
        _("From email"),
        type=Text,
        constant_use=ConstantUse.VARIABLE_OR_CONSTANT,
        required=False,
        help_text=_(
            'Override the default from email to be used. '
            'It can either be binded to a variable or be a constant like '
            'support@store.com or even "Store Support" <support@store.com>.'
        )
    )
    language = Binding(_("Language"), type=Language, constant_use=ConstantUse.VARIABLE_OR_CONSTANT, required=True)
    fallback_language = Binding(
        _("Fallback language"), type=Language, constant_use=ConstantUse.CONSTANT_ONLY,
        default=settings.PARLER_DEFAULT_LANGUAGE_CODE
    )
    send_identifier = Binding(
        _("Send Identifier"), type=Text, constant_use=ConstantUse.CONSTANT_ONLY, required=False,
        help_text=_(
            "If set, this identifier will be logged into the event's log target. If the identifier has already "
            "been logged, the e-mail won't be sent again."
        )
    )

    def __init__(self, *args, **kwargs):
        # force refresh the lis of options
        self.template_fields["email_template"].choices = [(None, "-----")] + [
            (template.pk, template.name)
            for template in EmailTemplate.objects.all()
        ]
        super().__init__(*args, **kwargs)

    def execute(self, context):
        """
        :param context: Script Context.
        :type context: shuup.notify.script.Context
        """
        recipient = get_email_list(self.get_value(context, "recipient"))
        if not recipient:
            context.log(logging.INFO, "Info! %s: Not sending mail, no recipient.", self.identifier)
            return

        send_identifier = self.get_value(context, "send_identifier")
        if send_identifier and context.log_entry_queryset.filter(identifier=send_identifier).exists():
            context.log(
                logging.INFO,
                "Info! %s: Not sending mail, it was already sent (%r).",
                self.identifier,
                send_identifier
            )
            return

        languages = [language for language in [
            self.get_value(context, "language"),
            self.get_value(context, "fallback_language"),
        ] if language and language in dict(settings.LANGUAGES).keys()]

        if not languages:
            languages = [settings.PARLER_DEFAULT_LANGUAGE_CODE]

        strings = self.get_template_values(context, languages)

        subject = unescape(strings.get("subject"))
        body = unescape(strings.get("body"))
        email_template_id = strings.get("email_template")

        if email_template_id:
            email_template = EmailTemplate.objects.filter(pk=email_template_id).first()

            if email_template and "%html_body%" in email_template.template:
                body = email_template.template.replace("%html_body%", body)

        content_type = strings.get("content_type")
        if not (subject and body):
            context.log(
                logging.INFO,
                "Info! %s: Not sending mail to %s, either subject or body empty.",
                self.identifier,
                recipient
            )
            return

        reply_to = get_email_list(self.get_value(context, "reply_to_address"))
        from_email = self.get_value(context, "from_email")
        bcc = get_email_list(self.get_value(context, "bcc"))
        cc = get_email_list(self.get_value(context, "cc"))

        subject = " ".join(subject.splitlines())  # Email headers may not contain newlines
        message = EmailMessage(
            subject=subject,
            body=body,
            to=recipient,
            reply_to=reply_to,
            from_email=from_email,
            bcc=bcc,
            cc=cc
        )
        message.content_subtype = content_type
        notification_email_before_send.send(sender=type(self), action=self, message=message, context=context)
        message.send()
        context.log(logging.INFO, "Info! %s: Mail sent to %s.", self.identifier, recipient)

        notification_email_sent.send(sender=type(self), message=message, context=context)

        if send_identifier:
            context.add_log_entry_on_log_target("Info! Email sent to %s: %s" % (recipient, subject), send_identifier)


def get_email_list(email):
    return email.split(",") if email else []
