# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from copy import deepcopy

from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms.models import modelform_factory
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import MenuEntry
from shoop.admin.toolbar import (
    get_default_edit_toolbar, Toolbar, URLActionButton
)
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import PaymentMethod, ShippingMethod
from shoop.core.modules.interface import ModuleNotFound
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class MethodEditToolbar(Toolbar):
    def __init__(self, view_object):
        super(Toolbar, self).__init__()
        self.view_object = view_object
        get_default_edit_toolbar(toolbar=self, view_object=view_object, save_form_id="method_form")
        method = view_object.object
        if method.pk:
            self.build_detail_button(method)

    def build_detail_button(self, method):
        disable_reason = None
        try:
            if not method.module.admin_detail_view_class:
                disable_reason = _("The selected module has no details to configure")
        except ModuleNotFound:
            disable_reason = _("The selected module is not currently available")

        self.append(URLActionButton(
            url=reverse(
                "shoop_admin:%s.edit-detail" % self.view_object.action_url_name_prefix,
                kwargs={"pk": method.pk}
            ),
            text=_("Edit Details"),
            icon="fa fa-pencil",
            extra_css_class="btn-info",
            disable_reason=disable_reason
        ))


class _BaseMethodEditView(CreateOrUpdateView):
    model = None  # Overridden below
    action_url_name_prefix = None
    template_name = "shoop/admin/methods/edit.jinja"
    form_class = forms.Form
    context_object_name = "method"

    @property
    def title(self):
        return _(u"Edit %(model)s") % {"model": self.model._meta.verbose_name}

    def get_breadcrumb_parents(self):
        return [
            MenuEntry(
                text=force_text(self.model._meta.verbose_name_plural).title(),
                url="shoop_admin:%s.list" % self.action_url_name_prefix
            )
        ]

    def get_form(self, form_class=None):
        form_class = modelform_factory(
            model=self.model,
            form=MultiLanguageModelForm,
            fields=("name", "status", "tax_class", "module_identifier"),
            widgets={"module_identifier": forms.Select},
        )
        form = form_class(languages=settings.LANGUAGES, **self.get_form_kwargs())
        form.fields["module_identifier"].widget.choices = self.model.get_module_choices(
            empty_label=(_("Default %s module") % self.model._meta.verbose_name).title()
        )

        # Add fields from the module, if any...
        form.module_option_field_names = []
        for field_name, field in self.object.module.option_fields:
            form.fields[field_name] = deepcopy(field)
            form.module_option_field_names.append(field_name)
            if self.object.module_data and field_name in self.object.module_data:
                form.initial[field_name] = self.object.module_data[field_name]

        return form

    def get_success_url(self):
        return reverse("shoop_admin:%s.edit" % self.action_url_name_prefix, kwargs={"pk": self.object.pk})

    def get_toolbar(self):
        return MethodEditToolbar(self)

    def save_form(self, form):
        self.object = form.save()
        if not self.object.module_data:
            self.object.module_data = {}
        for field_name in form.module_option_field_names:
            if field_name in form.cleaned_data:
                self.object.module_data[field_name] = form.cleaned_data[field_name]
        self.object.save()


class ShippingMethodEditView(_BaseMethodEditView):
    model = ShippingMethod
    action_url_name_prefix = "method.shipping"


class PaymentMethodEditView(_BaseMethodEditView):
    model = PaymentMethod
    action_url_name_prefix = "method.payment"
