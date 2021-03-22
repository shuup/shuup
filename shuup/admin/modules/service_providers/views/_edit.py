# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import MenuEntry
from shuup.admin.toolbar import URLActionButton, get_default_edit_toolbar
from shuup.admin.utils.urls import get_model_url
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.apps.provides import get_provide_objects
from shuup.core.models import ServiceProvider
from shuup.core.utils.forms import FormInfoMap
from shuup.utils.django_compat import force_text, reverse, reverse_lazy


class ServiceProviderEditView(CreateOrUpdateView):
    model = ServiceProvider
    template_name = "shuup/admin/service_providers/edit.jinja"
    form_class = forms.Form  # Overridden in get_form
    context_object_name = "service_provider"
    form_provide_key = "service_provider_admin_form"
    add_form_errors_as_messages = True

    @property
    def title(self):
        return _("Edit %(model)s") % {"model": self.model._meta.verbose_name}

    def get_breadcrumb_parents(self):
        return [
            MenuEntry(
                text=force_text(self.model._meta.verbose_name_plural).title(), url="shuup_admin:service_provider.list"
            )
        ]

    def get_form(self, form_class=None):
        form_classes = list(get_provide_objects(self.form_provide_key))
        form_infos = FormInfoMap(form_classes)
        if self.object and self.object.pk:
            return self._get_concrete_form(form_infos)
        else:
            return self._get_type_choice_form(form_infos)

    def _get_concrete_form(self, form_infos):
        form_info = form_infos.get_by_object(self.object)
        self.form_class = form_info.form_class
        return self._get_form(form_infos, form_info, type_enabled=False)

    def _get_type_choice_form(self, form_infos):
        selected_type = self.request.GET.get("type")
        form_info = form_infos.get_by_choice_value(selected_type)
        if not form_info:
            form_info = list(form_infos.values())[0]
        self.form_class = form_info.form_class
        self.object = form_info.model()
        return self._get_form(form_infos, form_info, type_enabled=True)

    def _get_form(self, form_infos, selected, type_enabled):
        form = self.form_class(**self.get_form_kwargs())
        type_field = forms.ChoiceField(
            choices=form_infos.get_type_choices(),
            label=_("Type"),
            required=type_enabled,
            initial=selected.choice_value,
            help_text=_(
                "The service provider type. "
                "This can be any of the shipping carriers or payment processors configured for your shop."
            ),
        )
        if not type_enabled:
            type_field.widget.attrs["disabled"] = True
        form.fields["type"] = type_field
        return form

    def get_success_url(self):
        return reverse("shuup_admin:service_provider.edit", kwargs={"pk": self.object.pk})

    def get_toolbar(self):
        save_form_id = self.get_save_form_id()
        object = self.get_object()
        delete_url = reverse_lazy("shuup_admin:service_provider.delete", kwargs={"pk": object.pk})
        toolbar = get_default_edit_toolbar(self, save_form_id, delete_url=delete_url)
        if self.object.pk:
            toolbar.append(
                URLActionButton(
                    text=_("Create {service_name}").format(service_name=self.object.service_model._meta.verbose_name),
                    icon="fa fa-plus",
                    url="{model_url}?provider={id}".format(
                        model_url=get_model_url(self.object.service_model, "new"), id=self.object.id
                    ),
                    extra_css_class="btn-primary",
                )
            )

        return toolbar
