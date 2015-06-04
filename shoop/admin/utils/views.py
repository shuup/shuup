# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, UpdateView
from shoop.admin.toolbar import get_default_edit_toolbar, Toolbar, NewActionButton
from shoop.admin.utils.picotable import PicotableViewMixin
from shoop.admin.utils.urls import get_model_url, NoModelUrl, get_model_front_url
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class CreateOrUpdateView(UpdateView):
    def get_object(self, queryset=None):
        if not self.kwargs.get(self.pk_url_kwarg):
            return self.model()
        return super(CreateOrUpdateView, self).get_object(queryset)

    def get_toolbar(self):
        save_form_id = self.get_save_form_id()
        if save_form_id:
            return get_default_edit_toolbar(self, save_form_id)

    def get_context_data(self, **kwargs):
        context = super(CreateOrUpdateView, self).get_context_data(**kwargs)
        context["is_new"] = (not self.object.pk)
        context["front_url"] = get_model_front_url(self.request, self.object)
        context["title"] = get_create_or_change_title(self.request, self.object)
        context["save_form_id"] = self.get_save_form_id()
        context["toolbar"] = self.get_toolbar()
        return context

    def get_save_form_id(self):
        return getattr(self, "save_form_id", None) or "%s_form" % self.get_context_object_name(self.object)

    def get_return_url(self):
        return get_model_url(self.object, kind="list")

    def get_new_url(self):
        return get_model_url(self.object, kind="new")

    def get_success_url(self):
        next = self.request.REQUEST.get("__next")
        try:
            if next == "return":
                return self.get_return_url()
            elif next == "new":
                return self.get_new_url()
        except NoModelUrl:
            pass

        try:
            return super(CreateOrUpdateView, self).get_success_url()
        except ImproperlyConfigured:
            pass

        try:
            return get_model_url(self.object)
        except NoModelUrl:
            pass

    def get_form_kwargs(self):
        kwargs = super(CreateOrUpdateView, self).get_form_kwargs()
        form_class = getattr(self, "form_class", None)
        if form_class and issubclass(form_class, MultiLanguageModelForm):
            kwargs["languages"] = settings.LANGUAGES
        return kwargs


def add_create_or_change_message(request, instance, is_new):
    if is_new:
        messages.success(request, _(u"New %s created.") % instance._meta.verbose_name)
    else:
        messages.success(request, _(u"%s edited.") % instance._meta.verbose_name.title())


def get_create_or_change_title(request, instance, name_field=None):
    """
    Get a title suitable for an create-or-update view.

    :param request: Request
    :type request: HttpRequest
    :param instance: Model instance
    :type instance: django.db.models.Model
    :param name_field: Which property to try to read the name from. If None, use `str`
    :type name_field: str
    :return: Title
    :rtype: str
    """
    if not instance.pk:
        return _("New %s") % instance._meta.verbose_name

    if name_field:
        name = getattr(instance, name_field, None)
    else:
        name = "%s" % instance

    if name:
        return force_text(name)

    return _("Unnamed %s") % instance._meta.verbose_name


class PicotableListView(PicotableViewMixin, ListView):
    def get_toolbar(self):
        try:
            new_url = get_model_url(self.model, kind="new")
        except NoModelUrl:
            new_url = None

        if new_url:
            return Toolbar([NewActionButton(new_url)])

    def get_context_data(self, **kwargs):
        context = super(PicotableListView, self).get_context_data(**kwargs)
        context["toolbar"] = self.get_toolbar()
        return context
