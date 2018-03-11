# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

import six
from django.core.urlresolvers import reverse_lazy
from django.forms import TimeInput as DjangoTimeInput
from django.forms import HiddenInput, Select, SelectMultiple, Textarea, Widget
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from filer.models import File

from shuup.admin.utils.forms import flatatt_filter
from shuup.admin.utils.urls import get_model_url, NoModelUrl
from shuup.core.models import (
    Contact, PersonContact, Product, ProductMode, ShopProduct
)


class BasePopupChoiceWidget(Widget):
    browse_kind = None
    filter = None

    def __init__(self, attrs=None, clearable=False, empty_text=u"\u2014"):
        self.clearable = clearable
        self.empty_text = empty_text
        super(BasePopupChoiceWidget, self).__init__(attrs)

    def get_browse_markup(self):
        icon = "<i class='fa fa-folder'></i>"
        return "<button class='browse-btn btn btn-info btn-sm' type='button'>%(icon)s %(text)s</button>" % {
            "icon": icon,
            "text": _("Browse")
        }

    def get_clear_markup(self):
        icon = "<i class='fa fa-cross'></i>"
        return "<button class='clear-btn btn btn-default btn-sm' type='button'>%(icon)s %(text)s</button>" % {
            "icon": icon,
            "text": _("Clear")
        }

    def render_text(self, obj):
        url = getattr(obj, "url", None)
        text = self.empty_text
        if obj:
            text = force_text(obj)
            if not url:
                try:
                    url = get_model_url(obj)
                except NoModelUrl:
                    pass
        if not url:
            url = "#"

        return mark_safe("<a class=\"browse-text\" href=\"%(url)s\" target=\"_blank\">%(text)s</a>&nbsp;" % {
            "text": escape(text),
            "url": escape(url),
        })

    def get_object(self, value):
        raise NotImplementedError("Not implemented")

    def render(self, name, value, attrs=None):
        if value:
            obj = self.get_object(value)
        else:
            obj = None
        pk_input = HiddenInput().render(name, value, attrs)
        media_text = self.render_text(obj)
        bits = [self.get_browse_markup(), pk_input, " ", media_text]

        if self.clearable:
            bits.insert(1, self.get_clear_markup())

        return mark_safe("<div %(attrs)s>%(content)s</div>" % {
            "attrs": flatatt_filter({
                "class": "browse-widget %s-browse-widget" % self.browse_kind,
                "data-browse-kind": self.browse_kind,
                "data-clearable": self.clearable,
                "data-empty-text": self.empty_text,
                "data-filter": self.filter
            }),
            "content": "".join(bits)
        })


class FileDnDUploaderWidget(Widget):
    def __init__(self, attrs=None, kind=None, upload_path="/", clearable=False):
        self.kind = kind
        self.upload_path = upload_path
        self.clearable = clearable
        super(FileDnDUploaderWidget, self).__init__(attrs)

    def _get_file_attrs(self, file):
        if not file:
            return []
        try:
            thumbnail = file.easy_thumbnails_thumbnailer.get_thumbnail({
                'size': (120, 120),
                'crop': True,
                'upscale': True,
                'subject_location': file.subject_location
            })
        except Exception:
            thumbnail = None
        data = {
            "id": file.id,
            "name": file.label,
            "size": file.size,
            "url": file.url,
            "thumbnail": (thumbnail.url if thumbnail else None),
            "date": file.uploaded_at.isoformat()
        }
        return ["data-%s='%s'" % (key, val) for key, val in six.iteritems(data) if val is not None]

    def render(self, name, value, attrs={}):
        pk_input = HiddenInput().render(name, value, attrs)
        file_attrs = [
            "data-upload_path='%s'" % self.upload_path,
            "data-add_remove_links='%s'" % self.clearable,
            "data-dropzone='true'"
        ]
        if self.kind:
            file_attrs.append("data-kind='%s'" % self.kind)
        if value:
            file = File.objects.filter(pk=value).first()
            file_attrs += self._get_file_attrs(file)
        return (
            mark_safe("<div id='%s-dropzone' class='dropzone %s' %s>%s</div>" % (
                attrs.get("id", "dropzone"),
                "has-file" if value else "",
                " ".join(file_attrs),
                pk_input
            ))
        )


class TextEditorWidget(Textarea):
    def render(self, name, value, attrs=None):
        attrs_for_textarea = attrs.copy()
        attrs_for_textarea['class'] = 'hidden'
        attrs_for_textarea['id'] += '-textarea'
        html = super(TextEditorWidget, self).render(name, value, attrs_for_textarea)
        return mark_safe(
            "<div id='%s-editor-wrap' class='summernote-wrap'>%s<div class='summernote-editor'>%s</div></div>" % (
                attrs["id"], html, value or ""
            )
        )


class MediaChoiceWidget(BasePopupChoiceWidget):
    browse_kind = "media"

    def get_object(self, value):
        return File.objects.get(pk=value)


class ImageChoiceWidget(MediaChoiceWidget):
    filter = "images"


class ProductChoiceWidget(BasePopupChoiceWidget):
    browse_kind = "product"

    def get_object(self, value):
        return Product.objects.get(pk=value)


class ShopProductChoiceWidget(BasePopupChoiceWidget):
    browse_kind = "shop_product"

    def get_object(self, value):
        return ShopProduct.objects.get(pk=value)


class ContactChoiceWidget(BasePopupChoiceWidget):
    browse_kind = "contact"

    def get_object(self, value):
        return Contact.objects.get(pk=value)

    def get_browse_markup(self):
        icon = "<i class='fa fa-user'></i>"
        return "<button class='browse-btn btn btn-info btn-sm' type='button'>%(icon)s %(text)s</button>" % {
            "icon": icon,
            "text": _("Select")
        }


class PersonContactChoiceWidget(ContactChoiceWidget):

    @property
    def filter(self):
        return json.dumps({"groups": [PersonContact.get_default_group().pk]})


class PackageProductChoiceWidget(ProductChoiceWidget):
    filter = json.dumps({"modes": [ProductMode.NORMAL.value, ProductMode.VARIATION_CHILD.value]})


class QuickAddRelatedObjectSelect(Select):
    url = ""
    model = ""

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(base_attrs=attrs, extra_attrs={"name": name})
        if self.model:
            final_attrs['data-model'] = self.model
            choices = []
        output = [format_html('<select{}>', flatatt(final_attrs))]
        options = self.render_options(choices, [value])
        if options:
            output.append(options)
        output.append('</select>')
        quick_add_button = """
            <span class="quick-add-btn">
                <a
                    class="btn"
                    data-url="%s?mode=iframe&quick_add_target=%s"
                    data-toggle="popover"
                    data-placement="bottom"
                    data-trigger="manual"
                    data-content="%s">
                        <i class="fa fa-plus text-primary"></i>
                </a>
            </span>
        """.strip()
        output.append(quick_add_button % (self.url, name, _("Create New")))
        return mark_safe('\n'.join(output))


class QuickAddRelatedObjectMultiSelect(SelectMultiple):
    url = ""

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = []
        final_attrs = self.build_attrs(base_attrs=attrs, extra_attrs={"name": name})
        output = [format_html('<select multiple="multiple"{}>', flatatt(final_attrs))]
        options = self.render_options(choices, value)
        if options:
            output.append(options)
        output.append('</select>')
        quick_add_button = """
            <span class="quick-add-btn">
                <a
                    class="btn"
                    data-url="%s?mode=iframe&quick_add_target=%s"
                    data-toggle="popover"
                    data-placement="bottom"
                    data-trigger="hover"
                    data-content="%s">
                        <i class="fa fa-plus text-primary"></i>
                </a>
            </span>
        """.strip()
        output.append(quick_add_button % (self.url, name, _("Create New")))
        return mark_safe('\n'.join(output))


class QuickAddCategoryMultiSelect(QuickAddRelatedObjectMultiSelect):
    url = reverse_lazy("shuup_admin:category.new")


class QuickAddCategorySelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:category.new")


class QuickAddProductTypeSelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:product_type.new")


class QuickAddManufacturerSelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:manufacturer.new")
    model = "shuup.Manufacturer"


class QuickAddPaymentMethodsSelect(QuickAddRelatedObjectMultiSelect):
    url = reverse_lazy("shuup_admin:payment_method.new")


class QuickAddShippingMethodsSelect(QuickAddRelatedObjectMultiSelect):
    url = reverse_lazy("shuup_admin:shipping_method.new")


class QuickAddUserMultiSelect(QuickAddRelatedObjectMultiSelect):
    url = reverse_lazy("shuup_admin:user.new")


class TimeInput(DjangoTimeInput):
    input_type = "time"
