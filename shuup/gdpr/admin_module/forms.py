# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.forms import BaseModelFormSet
from django.forms.formsets import DEFAULT_MAX_NUM, DEFAULT_MIN_NUM

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.admin.forms.widgets import (
    QuickAddRelatedObjectMultiSelect, QuickAddRelatedObjectSelect,
    TextEditorWidget
)
from shuup.admin.shop_provider import get_shop
from shuup.gdpr.models import GDPRCookieCategory, GDPRSettings
from shuup.gdpr.utils import get_possible_consent_pages
from shuup.utils.multilanguage_model_form import (
    MultiLanguageModelForm, to_language_codes
)


class QuickAddPageSelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:simple_cms.page.new")


class QuickAddPageMultiSelect(QuickAddRelatedObjectMultiSelect):
    url = reverse_lazy("shuup_admin:simple_cms.page.new")


class GDPRSettingsForm(MultiLanguageModelForm):
    class Meta:
        exclude = ("shop",)
        model = GDPRSettings
        widgets = {
            "auth_consent_text": TextEditorWidget(),
            "cookie_banner_content": TextEditorWidget(),
            "cookie_privacy_excerpt": TextEditorWidget(),
            "privacy_policy_page": QuickAddPageSelect(editable_model="shuup_simple_cms.Page"),
            "consent_pages": QuickAddPageMultiSelect()
        }

    def __init__(self, **kwargs):
        self.request = kwargs.pop("request")
        super(GDPRSettingsForm, self).__init__(**kwargs)
        shop = get_shop(self.request)
        choices = [(p.id, p.title) for p in get_possible_consent_pages(shop)]
        self.fields["privacy_policy_page"].choices = choices
        self.fields["consent_pages"].required = False
        self.fields["consent_pages"].choices = choices


class GDPRCookieCategoryForm(MultiLanguageModelForm):
    class Meta:
        exclude = ("shop",)
        model = GDPRCookieCategory


class GDPRBaseFormPart(FormPart):
    priority = -1000

    def get_form_defs(self):
        yield TemplatedFormDef(
            "base",
            GDPRSettingsForm,
            template_name="shuup/admin/gdpr/edit_base_form_part.jinja",
            required=True,
            kwargs={
                "instance": self.object,
                "languages": settings.LANGUAGES,
                "request": self.request
            }
        )

    def form_valid(self, form):
        self.object = form["base"].save()


class GDPRCookieCategoryFormSet(BaseModelFormSet):
    form_class = GDPRCookieCategoryForm
    validate_min = False
    can_delete = True
    can_order = False
    validate_max = False
    min_num = DEFAULT_MIN_NUM
    max_num = DEFAULT_MAX_NUM
    absolute_max = DEFAULT_MAX_NUM
    model = GDPRCookieCategory
    extra = 1

    def __init__(self, *args, **kwargs):
        self.shop = kwargs.pop("shop")
        self.default_language = kwargs.pop(
            "default_language", getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE"))
        self.languages = to_language_codes(kwargs.pop("languages", ()), self.default_language)
        kwargs.pop("empty_permitted", None)  # this is unknown to formset
        super(GDPRCookieCategoryFormSet, self).__init__(*args, **kwargs)

    def get_queryset(self):
        return GDPRCookieCategory.objects.filter(shop=self.shop)

    def form(self, **kwargs):
        kwargs.setdefault("languages", self.languages)
        return self.form_class(**kwargs)

    def save(self, commit=True):
        forms = self.forms or []
        for form in forms:
            form.instance.shop = self.shop
        super(GDPRCookieCategoryFormSet, self).save(commit)


class GDPRCookieCategoryFormPart(FormPart):
    name = "cookie_categories"
    formset = GDPRCookieCategoryFormSet

    def get_form_defs(self):
        yield TemplatedFormDef(
            self.name,
            self.formset,
            template_name="shuup/admin/gdpr/edit_cookie_category_form_part.jinja",
            required=False,
            kwargs={
                "shop": self.object.shop,
                "languages": settings.LANGUAGES,
            }
        )

    def form_valid(self, form):
        if self.name in form.forms:
            form.forms[self.name].save()
