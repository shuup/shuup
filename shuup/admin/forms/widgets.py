# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

import six
from django.forms import HiddenInput, Textarea, TextInput
from django.forms import TimeInput as DjangoTimeInput
from django.forms import Widget
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from filer.models import File

from shuup.admin.forms.quick_select import (
    QuickAddRelatedObjectMultiSelect, QuickAddRelatedObjectSelect
)
from shuup.admin.utils.forms import flatatt_filter
from shuup.admin.utils.urls import get_model_url, NoModelUrl
from shuup.core.models import (
    Contact, PersonContact, Product, ProductMode, ShopProduct
)
from shuup.utils.django_compat import force_text, reverse_lazy


class BasePopupChoiceWidget(Widget):
    browse_kind = None
    filter = None
    browse_text = _("Select")
    select_icon = "fa fa-folder"
    clear_icon = "fa fa-trash"
    external_icon = "fa fa-external-link"

    def __init__(self, attrs=None, clearable=False, empty_text=True):
        self.clearable = clearable
        self.empty_text = empty_text
        super(BasePopupChoiceWidget, self).__init__(attrs)

    def get_browse_markup(self):
        return """
            <button class='browse-btn btn btn-primary btn-sm' type='button'><i class='%(icon)s'></i> %(text)s</button>
        """ % {
            "icon": self.select_icon,
            "text": self.browse_text
        }

    def get_clear_markup(self):
        return "<button class='clear-btn btn btn-danger btn-sm' type='button'><i class='%(icon)s'></i></button>" % {
            "icon": self.clear_icon
        }

    def render_text(self, obj):
        url = getattr(obj, "url", None)
        text = ""
        if obj:
            text = force_text(obj)
            self.empty_text = False
            if not url:
                try:
                    url = get_model_url(obj)
                except NoModelUrl:
                    pass

        if not url:
            url = "#"

        css_style = ""

        if self.empty_text or not text:
            css_style = "display: none"

        icon = "<i class='%s'></i>" % self.external_icon

        return mark_safe(
            ("<a class=\"btn btn-inverse browse-text btn-sm\" style=\"%(css_style)s\" \
            href=\"%(url)s\" target=\"_blank\">%(icon)s %(text)s</a>") % {
                "css_style": css_style,
                "icon": icon,
                "text": escape(text),
                "url": escape(url),
            })

    def get_object(self, value):
        raise NotImplementedError("Error! Not implemented: `BasePopupChoiceWidget` -> `get_object()`.")

    def render(self, name, value, attrs=None, renderer=None):
        if value:
            obj = self.get_object(value)
        else:
            obj = None
        pk_input = HiddenInput().render(name, value, attrs)
        media_text = self.render_text(obj)
        bits = [self.get_browse_markup(), pk_input, " ", media_text]

        if self.clearable:
            bits.append(self.get_clear_markup())

        return mark_safe("<div %(attrs)s>%(content)s</div>" % {
            "attrs": flatatt_filter({
                "class": "browse-widget %s-browse-widget d-flex mr-auto align-items-center" % self.browse_kind,
                "data-browse-kind": self.browse_kind,
                "data-clearable": self.clearable,
                "data-empty-text": self.empty_text,
                "data-filter": self.filter
            }),
            "content": "".join(bits)
        })


class FileDnDUploaderWidget(Widget):
    def __init__(self, attrs=None, kind=None, upload_path="/", clearable=False,
                 browsable=True, upload_url=None, dropzone_attrs={}):
        self.kind = kind
        self.upload_path = upload_path
        self.clearable = clearable
        self.browsable = browsable
        self.dropzone_attrs = dropzone_attrs

        if upload_url is None:
            upload_url = reverse_lazy("shuup_admin:media.upload")
        self.upload_url = upload_url
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

    def render(self, name, value, attrs={}, renderer=None):
        pk_input = HiddenInput().render(name, value, attrs)
        file_attrs = [
            "data-upload_path='%s'" % self.upload_path,
            "data-add_remove_links='%s'" % self.clearable,
            "data-dropzone='true'",
            "data-browsable='%s'" % self.browsable,
        ]
        if self.upload_url:
            file_attrs.append("data-upload_url='%s'" % self.upload_url)
        if self.kind:
            file_attrs.append("data-kind='%s'" % self.kind)

        if self.dropzone_attrs:
            # attributes passed here will be converted into keys with dz_ prefix
            # `{max-filesize: 1}` will be converted into `data-dz_max-filesize="1"`
            file_attrs.extend([
                'data-dz_{}="{}"'.format(k, force_text(v))
                for k, v in self.dropzone_attrs.items()
            ])

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
    def render(self, name, value, attrs=None, renderer=None):
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
    browse_text = _("Select Media")

    def get_object(self, value):
        return File.objects.get(pk=value)


class ImageChoiceWidget(MediaChoiceWidget):
    filter = "images"
    browse_text = _("Select Image")


class ProductChoiceWidget(BasePopupChoiceWidget):
    browse_kind = "product"
    browse_text = _("Select Product")

    def get_object(self, value):
        return Product.objects.get(pk=value)


class ShopProductChoiceWidget(BasePopupChoiceWidget):
    browse_kind = "shop_product"
    browse_text = _("Select Product")

    def get_object(self, value):
        return ShopProduct.objects.get(pk=value)


class ContactChoiceWidget(BasePopupChoiceWidget):
    browse_kind = "contact"
    browse_text = _("Select Contact")
    icon = "fa fa-user"

    def get_object(self, value):
        return Contact.objects.get(pk=value)

    def get_browse_markup(self):
        icon = "<i class='fa fa-user'></i>"
        return "<button class='browse-btn btn btn-primary btn-sm' type='button'>%(icon)s %(text)s</button>" % {
            "icon": icon,
            "text": self.browse_text
        }


class HexColorWidget(TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        field_attrs = attrs.copy()
        field_attrs["class"] = field_attrs.get("class", "") + " hex-color-picker"
        return super(HexColorWidget, self).render(name, value, field_attrs)


class CodeEditorWidget(Textarea):
    def render(self, name, value, attrs=None, renderer=None):
        attrs_for_textarea = attrs.copy()
        attrs_for_textarea["id"] += "-snippet"
        attrs_for_textarea["class"] += " code-editor-textarea"
        return super().render(name, value, attrs_for_textarea)


class CodeEditorWithHTMLPreview(Textarea):
    template_name = 'shuup/admin/forms/widgets/code_editor_with_preview.html'

    def render(self, name, value, attrs=None, renderer=None):
        attrs_for_textarea = attrs.copy()
        attrs_for_textarea["id"] += "-snippet"
        attrs_for_textarea["class"] += " code-editor-textarea code-editor-with-preview"
        return super().render(name, value, attrs_for_textarea)


class PersonContactChoiceWidget(ContactChoiceWidget):

    @property
    def filter(self):
        return json.dumps({"groups": [PersonContact.get_default_group().pk]})


class PackageProductChoiceWidget(ProductChoiceWidget):
    filter = json.dumps({"modes": [ProductMode.NORMAL.value, ProductMode.VARIATION_CHILD.value]})


class QuickAddSupplierMultiSelect(QuickAddRelatedObjectMultiSelect):
    url = reverse_lazy("shuup_admin:supplier.new")
    model = "shuup.Supplier"


class QuickAddCategoryMultiSelect(QuickAddRelatedObjectMultiSelect):
    url = reverse_lazy("shuup_admin:category.new")
    model = "shuup.Category"


class QuickAddCategorySelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:category.new")
    model = "shuup.Category"


class QuickAddProductTypeSelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:product_type.new")
    model = "shuup.ProductType"


class QuickAddTaxGroupSelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:customer_tax_group.new")
    model = "shuup.CustomerTaxGroup"


class QuickAddTaxClassSelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:tax_class.new")


class QuickAddSalesUnitSelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:sales_unit.new")


class QuickAddDisplayUnitSelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:display_unit.new")


class QuickAddManufacturerSelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:manufacturer.new")
    model = "shuup.Manufacturer"


class QuickAddPaymentMethodsSelect(QuickAddRelatedObjectMultiSelect):
    url = reverse_lazy("shuup_admin:payment_method.new")


class QuickAddShippingMethodsSelect(QuickAddRelatedObjectMultiSelect):
    url = reverse_lazy("shuup_admin:shipping_method.new")


class QuickAddUserMultiSelect(QuickAddRelatedObjectMultiSelect):
    url = reverse_lazy("shuup_admin:user.new")


class QuickAddContactGroupSelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:contact_group.new")


class QuickAddContactGroupMultiSelect(QuickAddRelatedObjectMultiSelect):
    url = reverse_lazy("shuup_admin:contact_group.new")


class QuickAddLabelMultiSelect(QuickAddRelatedObjectMultiSelect):
    url = reverse_lazy("shuup_admin:label.new")


class TimeInput(DjangoTimeInput):
    input_type = "time"
