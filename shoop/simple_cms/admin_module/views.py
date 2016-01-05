# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.forms import DateTimeField
from django.utils.translation import ugettext_lazy as _

from shoop.admin.utils.picotable import Column, TextFilter
from shoop.admin.utils.views import CreateOrUpdateView, PicotableListView
from shoop.simple_cms.models import Page
from shoop.utils.i18n import get_language_name
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class PageForm(MultiLanguageModelForm):
    available_from = DateTimeField(label=_("Available from"), required=False, localize=True)
    available_to = DateTimeField(label=_("Available to"), required=False, localize=True)

    class Meta:
        model = Page
        fields = [
            'title',
            'url',
            'content',
            'available_from',
            'available_to',
            'identifier',
            'visible_in_menu'
        ]

    def __init__(self, **kwargs):
        kwargs.setdefault("required_languages", ())  # No required languages here
        super(PageForm, self).__init__(**kwargs)

    def clean(self):
        """
        If title or content has been given on any language
        we must enforce that the other fields are also required in
        that language.

        This is done the way it is because url is not
        required by default in model level.
        """
        data = super(PageForm, self).clean()

        something_filled = False
        for language, field_names in self.trans_name_map.items():
            if not any(data.get(field_name) for field_name in field_names.values()):
                # Let's not complain about this language
                continue
            something_filled = True
            for field_name in field_names.values():
                value = data.get(field_name)
                if value:  # No need to bother complaining about this field
                    if field_name.startswith("url__"):  # url needs a second look though
                        if not self.is_url_valid(language, field_name, value):
                            self.add_error(field_name, ValidationError(_("URL already exists."), code="invalid_url"))
                    continue
                self.add_error(
                    field_name,
                    _("%(label)s is required when any %(language)s field is filled.") % {
                        "label": self.fields[field_name].label,
                        "language": get_language_name(language)
                    }
                )

        if not something_filled:
            titlefield = "title__%s" % self.default_language
            self.add_error(titlefield, _("Please fill at least one language fully."))

        return data

    def is_url_valid(self, language_code, field_name, url):
        """
        Ensure URL given is unique.

        Check through the pages translation model objects to make
        sure that the url given doesn't already exist.

        Possible failure cases:
        for new page:
        * URL already exists

        for existing page:
        * URL (other than owned by existing page) exists
        * URL exists in other languages of existing page
        """
        qs = self._get_translation_model().objects.filter(url=url)
        if not self.instance.pk:
            if qs.exists():
                return False
        other_qs = qs.exclude(master=self.instance)
        if other_qs.exists():
            return False
        own_qs = qs.filter(master=self.instance).exclude(language_code=language_code)
        if own_qs.exists():
            return False
        return True

    def _save_translation(self, instance, translation):
        if not translation.url:  # No url? Skip saving this.
            if translation.pk:  # Oh, it's an old one?
                translation.delete()  # Well, it's not anymore.
            return
        translation.save()


class PageEditView(CreateOrUpdateView):
    model = Page
    template_name = "shoop/simple_cms/admin/edit.jinja"
    form_class = PageForm
    context_object_name = "page"
    add_form_errors_as_messages = True

    def save_form(self, form):
        self.object = form.save()
        if not self.object.created_by:
            self.object.created_by = self.request.user
        self.object.modified_by = self.request.user
        self.object.save()


class PageListView(PicotableListView):
    model = Page
    columns = [
        Column(
            "title", _(u"Title"), sort_field="translations__title", display="title", linked=True,
            filter_config=TextFilter(operator="startswith")
        ),
        Column("available_from", _(u"Available from")),
        Column("available_to", _(u"Available to")),
        Column("created_by", _(u"Created by")),
        Column("created_on", _(u"Date created")),
    ]

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % (instance or _("Page")), "class": "header"},
            {"title": _(u"Available from"), "text": item["available_from"]},
            {"title": _(u"Available to"), "text": item["available_to"]} if instance.available_to else None
        ]
