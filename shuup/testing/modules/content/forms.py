# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from datetime import datetime
from django import forms
from django.conf import settings
from django.template import loader as template_loader
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from logging import getLogger

from shuup import configuration as config
from shuup.utils import djangoenv
from shuup.utils.django_compat import force_text

from . import data as content_data

# tries to import xtheme stuff
if djangoenv.has_installed("shuup.xtheme"):
    from shuup.xtheme import XTHEME_GLOBAL_VIEW_NAME
    from shuup.xtheme._theme import get_current_theme
    from shuup.xtheme.layout import Layout
    from shuup.xtheme.models import SavedViewConfig, SavedViewConfigStatus
    from shuup.xtheme.plugins.snippets import SnippetsPlugin


logger = getLogger(__name__)

BEHAVIOR_ORDER_CONFIRM_KEY = "behavior_order_confirm_script_pk"
CONTENT_FOOTER_KEY = "content_footer_pk"


class BehaviorWizardForm(forms.Form):
    order_confirm_notification = forms.BooleanField(
        label=_("Send customer order confirmation email"),
        required=False,
        initial=True,
        help_text=_(
            "We will configure a notification "
            "to send the customer an email "
            "after a placed order. "
            "You can disable this option later "
            "or even change the layout of the email."
        ),
    )

    def __init__(self, **kwargs):
        self.shop = kwargs.pop("shop")
        super(BehaviorWizardForm, self).__init__(**kwargs)

        if self._get_saved_script():
            self.fields["order_confirm_notification"].widget = forms.CheckboxInput(attrs={"disabled": True})

    def _get_saved_script(self):
        """ Returns the saved script from the DB, if it exists """
        from shuup.notify.models.script import Script

        return Script.objects.filter(pk=config.get(self.shop, BEHAVIOR_ORDER_CONFIRM_KEY)).first()

    def _get_send_email_action(self):
        from shuup.notify.actions import SendEmail

        current_language = translation.get_language()

        action_data = {
            "template_data": {},
            "recipient": {"variable": "customer_email"},
            "language": {"variable": "language"},
            "fallback_language": {"constant": current_language},
        }

        # fill the content and subject with the translations
        for language, __ in settings.LANGUAGES:
            try:
                translation.activate(language)

                action_data["template_data"][language] = {
                    "content_type": content_data.ORDER_CONFIRMATION["content_type"],
                    "subject": force_text(content_data.ORDER_CONFIRMATION["subject"]),
                    "body": template_loader.render_to_string(content_data.ORDER_CONFIRMATION["body_template"]).strip(),
                }

            except Exception:
                logger.exception("Error! Failed to translate language %s." % language)

                action_data["template_data"][language] = {"content_type": "text", "body": " ", "subject": " "}

        # Back to the old language.
        translation.activate(current_language)

        return SendEmail(action_data)

    def save(self):
        """ Create and configure the selected objects if needed. """

        # User wants an order notification and Notify installed and there is no script created previously.
        if (
            self.is_valid()
            and self.cleaned_data["order_confirm_notification"]
            and djangoenv.has_installed("shuup.notify")
            and not self._get_saved_script()
        ):

            from shuup.front.notify_events import OrderReceived
            from shuup.notify.models.script import Script
            from shuup.notify.script import Step, StepNext

            send_email_action = self._get_send_email_action()

            script = Script(
                event_identifier=OrderReceived.identifier, name="Order Received", enabled=True, shop=self.shop
            )
            script.set_steps([Step(next=StepNext.STOP, actions=(send_email_action,))])
            script.save()

            # Save the PK in the configs.
            config.set(self.shop, BEHAVIOR_ORDER_CONFIRM_KEY, script.pk)


class ContentWizardForm(forms.Form):
    def __init__(self, **kwargs):
        self.shop = kwargs.pop("shop")
        if not self.shop:
            raise ValueError("Error! No shop provided.")
        super(ContentWizardForm, self).__init__(**kwargs)

        if djangoenv.has_installed("shuup.simple_cms"):
            pages = self._get_installed_pages()

            self.fields["about_us"] = forms.BooleanField(
                label=_("Create About Us page"),
                required=False,
                initial=True,
                widget=forms.CheckboxInput(attrs={"disabled": (content_data.ABOUT_US_KEY in pages)}),
            )

            # Set the help text for different ocasions - whether the content is installed or not.
            if content_data.ABOUT_US_KEY in pages:
                self.fields["about_us"].help_text = _(
                    "We have already created an 'About Us' template for you based "
                    "on your shop information. You must review the page and "
                    "change it accordingly."
                )
            else:
                self.fields["about_us"].help_text = _(
                    "We will create an 'About Us' template for you. "
                    "We will base content of the page on your shop information. "
                    "After we are done, you must review the page and "
                    "change it accordingly."
                )

            self.fields["privacy_policy"] = forms.BooleanField(
                label=_("Create Privacy Policy page"),
                required=False,
                initial=True,
                widget=forms.CheckboxInput(attrs={"disabled": (content_data.PRIVACY_POLICY_KEY in pages)}),
            )
            # Set the help text for different ocasions - whether the content is installed or not.
            if content_data.PRIVACY_POLICY_KEY in pages:
                self.fields["privacy_policy"].help_text = _(
                    "We have already created a 'Privacy Policy' template "
                    "for you based on your shop information. "
                    "You must review the page and change it accordingly."
                )
            else:
                self.fields["privacy_policy"].help_text = _(
                    "We will create a 'Privacy Policy' template for you. "
                    "We will base content of the page on "
                    "your shop information. After we are done, "
                    "you must review the page and change it accordingly."
                )

            self.fields["terms_conditions"] = forms.BooleanField(
                label=_("Create Terms and Conditions page"),
                required=False,
                initial=True,
                widget=forms.CheckboxInput(attrs={"disabled": (content_data.TERMS_AND_CONDITIONS_KEY in pages)}),
            )
            # Set the help text for different ocasions - whether the content is installed or not.
            if content_data.TERMS_AND_CONDITIONS_KEY in pages:
                self.fields["terms_conditions"].help_text = _(
                    "We have already created a 'Terms & Conditions' template "
                    "for you based on your shop information. "
                    "You must review the page and change it accordingly."
                )
            else:
                self.fields["terms_conditions"].help_text = _(
                    "We will create a 'Terms & Conditions' template "
                    "for you. We will base content of the page on "
                    "your shop information. After we are done, "
                    "you must review the page and change it accordingly."
                )

            self.fields["refund_policy"] = forms.BooleanField(
                label=_("Create Refund Policy page"),
                required=False,
                initial=True,
                widget=forms.CheckboxInput(attrs={"disabled": (content_data.REFUND_POLICY_KEY in pages)}),
            )
            # Set the help text for different ocasions - whether the content is installed or not.
            if content_data.REFUND_POLICY_KEY in pages:
                self.fields["refund_policy"].help_text = _(
                    "We have already created a 'Refund Policy' template "
                    "for you based on your shop information. "
                    "You must review the page and change it accordingly."
                )
            else:
                self.fields["refund_policy"].help_text = _(
                    "We will create an 'Refund Policy' template for you. "
                    "We will base content of the page on your shop information. "
                    "After we are done, you must review the page and "
                    "change it accordingly."
                )

        if djangoenv.has_installed("shuup.xtheme"):
            from shuup.xtheme.models import SavedViewConfig

            svc_pk = config.get(self.shop, CONTENT_FOOTER_KEY)
            svc = SavedViewConfig.objects.filter(pk=svc_pk).first()

            self.fields["configure_footer"] = forms.BooleanField(
                label=_("Configure the footer"),
                required=False,
                initial=True,
                widget=forms.CheckboxInput(attrs={"disabled": bool(svc)}),
                help_text=_(
                    "We will now configure your shop footer and fill it with some of your shop's information. "
                    "Don't worry, you can change this at any time."
                ),
            )

    def _get_installed_pages(self):
        """
        Returns a dict[str, simple_cms.models.Page] of all installed pages by this form.
        """
        from shuup.simple_cms.models import Page

        return {
            page.identifier: page
            for page in Page.objects.for_shop(self.shop).filter(
                deleted=False, identifier__in=content_data.CMS_PAGES.keys()
            )
        }

    def save(self):
        """
        Generate the selected pages if SimpleCMS is installed.
        Generate the Footer if xTheme is installed.
        """
        if not self.is_valid():
            return

        # Form must be validated.
        if djangoenv.has_installed("shuup.simple_cms"):
            self._handle_simple_cms_save()

        if djangoenv.has_installed("shuup.xtheme") and self.cleaned_data["configure_footer"]:
            self._handle_xtheme_save()

    def _handle_simple_cms_save(self):
        pages = self._get_installed_pages()
        from shuup.simple_cms.models import Page

        create_about_us = self.cleaned_data["about_us"]
        create_privacy_policy = self.cleaned_data["privacy_policy"]
        create_terms_conditions = self.cleaned_data["terms_conditions"]
        create_refund_policy = self.cleaned_data["refund_policy"]

        context = {"shop": self.shop}

        page_create_map = [
            (create_about_us, content_data.ABOUT_US_KEY),
            (create_privacy_policy, content_data.PRIVACY_POLICY_KEY),
            (create_terms_conditions, content_data.TERMS_AND_CONDITIONS_KEY),
            (create_refund_policy, content_data.REFUND_POLICY_KEY),
        ]

        for create_page, page_identifier in page_create_map:
            # we must create the page because it is not created yet
            if create_page and page_identifier not in pages:
                template = content_data.CMS_PAGES[page_identifier]["template"]
                rendered_content = force_text(template_loader.render_to_string(template, context).strip())
                title = force_text(content_data.CMS_PAGES[page_identifier]["name"])

                Page.objects.create(
                    shop=self.shop,
                    identifier=page_identifier,
                    title=title,
                    content=rendered_content,
                    visible_in_menu=False,
                    url=page_identifier,
                    template_name=settings.SHUUP_SIMPLE_CMS_DEFAULT_TEMPLATE,
                    available_from=datetime.now(),
                )

    def _handle_xtheme_save(self):
        svc_pk = config.get(self.shop, CONTENT_FOOTER_KEY)
        svc = SavedViewConfig.objects.filter(pk=svc_pk).first()
        theme = get_current_theme(self.shop)

        if not svc and theme:
            context = {"shop": self.shop}
            rendered_content = template_loader.render_to_string(content_data.FOOTER_TEMPLATE, context).strip()
            layout = Layout(theme, "footer-bottom")
            # adds the footer template
            layout.begin_row()
            layout.begin_column({"md": 12})
            layout.add_plugin(SnippetsPlugin.identifier, {"in_place": rendered_content})

            svc = SavedViewConfig(
                theme_identifier=theme.identifier,
                shop=self.shop,
                view_name=XTHEME_GLOBAL_VIEW_NAME,
                status=SavedViewConfigStatus.CURRENT_DRAFT,
            )
            svc.set_layout_data(layout.placeholder_name, layout)
            svc.save()
            svc.publish()

            config.set(self.shop, CONTENT_FOOTER_KEY, svc.pk)
