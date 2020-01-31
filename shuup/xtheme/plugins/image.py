# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from filer.models import File

from shuup.admin.forms.widgets import ImageChoiceWidget
from shuup.xtheme import TemplatedPlugin
from shuup.xtheme.plugins.forms import TranslatableField


class ImagePluginChoiceWidget(ImageChoiceWidget):
    """
    Subclass of ImageChoiceWidget that will not raise an exception if
    given an invalid initial image ID (in case the image has been deleted).
    """
    def get_object(self, value):
        return File.objects.filter(pk=value).first()


class ImageIDField(forms.IntegerField):
    """
    A custom field that stores the ID value of a Filer image and presents
    Shuup admin's image popup widget.
    """
    widget = ImagePluginChoiceWidget(clearable=True)

    def clean(self, value):
        try:
            value = super(ImageIDField, self).clean(value)
        except ValidationError:
            raise ValidationError("Error! Invalid image ID.", code="invalid")
        return value


class ImagePlugin(TemplatedPlugin):
    """
    A linkable image plugin.
    """
    identifier = "images"
    name = _("Image")
    template_name = "shuup/xtheme/plugins/image.jinja"
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False)),
        ("image_id", ImageIDField(label=_("Image"), required=False)),
        ("url", forms.URLField(label=_("Image Link URL"), required=False)),
        ("full_width", forms.BooleanField(
            label=_("Full width"),
            required=False,
            initial=True,
            help_text=_("Set image to the full width of cell.")
        )),
        ("width", forms.IntegerField(
            label=_("Width (px)"),
            required=False,
            help_text=_("Leave blank for default width."),
        )),
        ("height", forms.IntegerField(
            label=_("Height (px)"),
            required=False,
            help_text=_("Leave blank for default width."),
        )),
    ]

    def get_context_data(self, context):
        """
        A custom get_context_data that returns the matching filer File.
        """
        image = None
        image_id = self.config.get("image_id", None)
        if image_id:
            image = File.objects.filter(pk=image_id).first()
        return {
            "title": self.get_translated_value("title", ""),
            "image": image,
            "url": self.config.get("url", None),
            "full_width": self.config.get("full_width", None),
            "width": self.config.get("width", None),
            "height": self.config.get("height", None),
        }
