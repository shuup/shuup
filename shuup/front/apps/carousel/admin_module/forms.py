# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.forms import BaseModelFormSet, ModelForm
from django.utils.timezone import now

from shuup.admin.forms.widgets import FileDnDUploaderWidget, HexColorWidget, ProductChoiceWidget, QuickAddCategorySelect
from shuup.admin.shop_provider import get_shop
from shuup.core.models import Category
from shuup.front.apps.carousel.models import Carousel, Slide
from shuup.simple_cms.models import Page
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm, to_language_codes


class CarouselForm(ModelForm):
    class Meta:
        model = Carousel
        exclude = ("shops",)
        widgets = {"arrows_color": HexColorWidget()}


class SlideForm(MultiLanguageModelForm):
    class Meta:
        model = Slide
        exclude = ("carousel",)
        widgets = {
            "active_dot_color": HexColorWidget(),
            "inactive_dot_color": HexColorWidget(),
            "category_link": QuickAddCategorySelect(editable_model="shuup.Category"),
        }

    def __init__(self, **kwargs):
        self.carousel = kwargs.pop("carousel")
        self.request = kwargs.pop("request")
        super(SlideForm, self).__init__(**kwargs)
        self.empty_permitted = False
        shop = get_shop(self.request)
        self.fields["category_link"].queryset = Category.objects.all_except_deleted(
            shop=self.request.shop
        ).prefetch_related("translations")
        self.fields["cms_page_link"].queryset = Page.objects.filter(shop=shop)
        self.fields["product_link"].widget = ProductChoiceWidget(clearable=True)
        for lang in self.languages:
            image_field = "image__%s" % lang
            self.fields[image_field].widget = FileDnDUploaderWidget(
                kind="images", upload_path="/carousel", clearable=True
            )
            if lang == self.default_language:
                self.fields[image_field].widget = FileDnDUploaderWidget(
                    kind="images", upload_path="/carousel", clearable=False
                )
                self.fields[image_field].required = True
                self.fields[image_field].widget.is_required = True

        if not self.fields["available_from"].initial:
            self.fields["available_from"].initial = now()

    def pre_master_save(self, instance):
        instance.carousel = self.carousel


class SlideFormSet(BaseModelFormSet):
    form_class = SlideForm
    model = Slide

    validate_min = False
    min_num = 0
    validate_max = False
    max_num = 20
    absolute_max = 20
    can_delete = True
    can_order = False
    extra = 0

    def __init__(self, *args, **kwargs):
        self.default_language = kwargs.pop("default_language", getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE"))
        self.carousel = kwargs.pop("carousel")
        self.languages = to_language_codes(kwargs.pop("languages", ()), self.default_language)
        self.request = kwargs.pop("request")
        super(SlideFormSet, self).__init__(*args, **kwargs)

    def get_queryset(self):
        return Slide.objects.filter(carousel=self.carousel)

    def form(self, **kwargs):
        kwargs.setdefault("carousel", self.carousel)
        kwargs.setdefault("languages", self.languages)
        kwargs.setdefault("default_language", settings.PARLER_DEFAULT_LANGUAGE_CODE)
        kwargs.setdefault("request", self.request)
        return self.form_class(**kwargs)
