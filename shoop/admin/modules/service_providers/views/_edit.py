# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from collections import OrderedDict

from django import forms
from django.core.urlresolvers import reverse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import MenuEntry
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.apps.provides import get_provide_objects
from shoop.core.models import ServiceProvider
from shoop.utils.iterables import first


class ServiceProviderEditView(CreateOrUpdateView):
    model = ServiceProvider
    template_name = "shoop/admin/service_providers/edit.jinja"
    form_class = forms.Form  # Overridden in get_form
    context_object_name = "service_provider"
    form_provide_key = "service_provider_admin_form"
    add_form_errors_as_messages = True

    @property
    def title(self):
        return _(u"Edit %(model)s") % {"model": self.model._meta.verbose_name}

    def get_breadcrumb_parents(self):
        return [
            MenuEntry(
                text=force_text(self.model._meta.verbose_name_plural).title(),
                url="shoop_admin:service_provider.list"
            )
        ]

    def get_form(self, form_class=None):
        form_classes = list(get_provide_objects(self.form_provide_key))
        form_infos = _FormInfoMap(form_classes)
        if self.object and self.object.pk:
            return self._get_concrete_form(form_infos)
        else:
            return self._get_type_choice_form(form_infos)

    def _get_concrete_form(self, form_infos):
        form_info = form_infos.get_by_object(self.object)
        self.form_class = form_info.form_class
        return self. _get_form(form_infos, form_info, type_enabled=False)

    def _get_type_choice_form(self, form_infos):
        selected_type = self.request.GET.get("type")
        form_info = form_infos.get_by_choice_value(selected_type)
        if not form_info:
            form_info = list(form_infos.values())[0]
        self.form_class = form_info.form_class
        self.object = form_info.model()
        return self. _get_form(form_infos, form_info, type_enabled=True)

    def _get_form(self, form_infos, selected, type_enabled):
        form = self.form_class(**self.get_form_kwargs())
        type_field = forms.ChoiceField(
            choices=form_infos.get_type_choices(),
            label=_("Type"),
            required=type_enabled,
            initial=selected.choice_value,
        )
        if not type_enabled:
            type_field.widget.attrs['disabled'] = True
        form.fields["type"] = type_field
        return form

    def get_success_url(self):
        return reverse("shoop_admin:service_provider.edit", kwargs={"pk": self.object.pk})


class _FormInfoMap(OrderedDict):
    def __init__(self, form_classes):
        form_infos = (_FormInfo(formcls) for formcls in form_classes)
        super(_FormInfoMap, self).__init__(
            (form_info.choice_value, form_info) for form_info in form_infos)

    def get_by_object(self, obj):
        return first(
            fi for fi in self.values() if isinstance(obj, fi.model))

    def get_by_choice_value(self, choice_value):
        return self.get(choice_value)

    def get_type_choices(self):
        return [(x.choice_value, x.choice_text) for x in self.values()]


class _FormInfo(object):
    def __init__(self, form_class):
        self.form_class = form_class
        self.model = form_class._meta.model
        modelmeta = self.model._meta
        self.choice_value = modelmeta.app_label + '.' + modelmeta.model_name
        self.choice_text = modelmeta.verbose_name.capitalize()
