# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup import configuration
from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.admin.forms.fields import ImageMultipleField
from shuup.admin.forms.widgets import FileDnDUploaderWidget


class TestShopForm(forms.Form):
    images = ImageMultipleField(
        label=_("Multiple Images"),
        required=False,
        widget=FileDnDUploaderWidget(
            kind="images",
            upload_path="/Shop",
            clearable=True,
            max_files=5
        )
    )

    def __init__(self, *args, **kwargs):
        self.shop = kwargs.pop("shop")
        super(TestShopForm, self).__init__(*args, **kwargs)
        self.fields["images"].initial = configuration.get(self.shop, "multiple_images_ids", [])

    def save(self, *args, **kwargs):
        images = [image.pk for image in self.cleaned_data.get("images", [])]
        configuration.set(self.shop, "multiple_images_ids", images)


class TestShopFormPart(FormPart):
    priority = 90
    name = "test_shop_form_part"

    def get_form_defs(self):
        yield TemplatedFormDef(
            self.name,
            form_class=TestShopForm,
            template_name="shuup_testing/shuup/admin/test_form_part.jinja",
            required=False,
            kwargs={
                "shop": self.object
            }
        )

    def form_valid(self, form):
        if form[self.name].has_changed():
            form[self.name].save()
