# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.http.response import HttpResponseNotAllowed
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import BaseDeleteView

from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.picotable import Column, TextFilter
from shuup.admin.utils.views import CreateOrUpdateView, PicotableListView
from shuup.apps.provides import get_provide_objects
from shuup.core import cache
from shuup.utils.django_compat import force_text, reverse_lazy
from shuup.xtheme.admin_module.widgets import XthemeCodeEditorWidget
from shuup.xtheme.models import Snippet
from shuup.xtheme.resources import GLOBAL_SNIPPETS_CACHE_KEY


class SnippetForm(forms.ModelForm):
    class Meta:
        model = Snippet
        fields = ["location", "themes", "snippet_type", "snippet"]
        widgets = {"snippet": XthemeCodeEditorWidget()}

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(SnippetForm, self).__init__(*args, **kwargs)

        themes_choices = [(theme.identifier, theme.name) for theme in get_provide_objects("xtheme") if theme.identifier]
        self.fields["themes"] = forms.MultipleChoiceField(
            choices=themes_choices,
            required=False,
            help_text=_(
                "Select the themes that will have this snippet injected. Leave the field blank to inject in all themes."
            ),
        )

        from shuup.xtheme.resources import LOCATION_INFO

        location_choices = [(location_name, location["name"]) for location_name, location in LOCATION_INFO.items()]
        self.fields["location"] = forms.ChoiceField(
            choices=location_choices, help_text=_("Select the location of the page to inject the snippet.")
        )

    def save(self, commit=True):
        self.instance.shop = get_shop(self.request)
        return super(SnippetForm, self).save(commit)

    def clean_themes(self):
        return ",".join(self.cleaned_data["themes"])


class SnippetEditView(CreateOrUpdateView):
    model = Snippet
    form_class = SnippetForm
    template_name = "shuup/xtheme/admin/snippet_edit.jinja"
    context_object_name = "snippet"

    def get_toolbar(self):
        save_form_id = self.get_save_form_id()
        if save_form_id:
            delete_url = None
            if self.object and self.object.pk:
                delete_url = reverse_lazy("shuup_admin:xtheme_snippet.delete", kwargs={"pk": self.object.pk})
            return get_default_edit_toolbar(self, save_form_id, delete_url=delete_url)

    def get_queryset(self):
        return Snippet.objects.filter(shop=get_shop(self.request))

    def form_valid(self, form):
        response = super(SnippetEditView, self).form_valid(form)
        shop = get_shop(self.request)
        cache_key = GLOBAL_SNIPPETS_CACHE_KEY.format(shop_id=shop.pk)
        cache.bump_version(cache_key)
        return response

    def get_form_kwargs(self):
        kwargs = super(SnippetEditView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class SnippetListView(PicotableListView):
    model = Snippet
    default_columns = [
        Column(
            "location",
            _("Location"),
            sort_field="location",
            filter_config=TextFilter(filter_field="location", placeholder=_("Filter by location...")),
        ),
        Column("snippet_type", _("Type"), sort_field="snippet_type"),
        Column("themes", _("Themes"), display="get_themes"),
    ]

    def get_themes(self, value):
        return ", ".join(
            [force_text(theme.name) for theme in get_provide_objects("xtheme") if theme.identifier in value.themes]
        )

    def get_queryset(self):
        return Snippet.objects.filter(shop=get_shop(self.request))


class SnippetDeleteView(BaseDeleteView):
    model = Snippet
    success_url = reverse_lazy("shuup_admin:xtheme_snippet.list")

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["post", "delete"])

    def get_queryset(self):
        return Snippet.objects.filter(shop=get_shop(self.request))

    def delete(self, request, *args, **kwargs):
        response = super(SnippetDeleteView, self).delete(request, *args, **kwargs)
        shop = get_shop(self.request)
        cache_key = GLOBAL_SNIPPETS_CACHE_KEY.format(shop_id=shop.pk)
        cache.bump_version(cache_key)
        return response
