# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.admin.forms import ShuupAdminForm
from shuup.simple_cms.models import PageOpenGraph


class CMSOpenGraphForm(ShuupAdminForm):
    class Meta:
        model = PageOpenGraph
        fields = ("og_type", "title", "description", "section", "tags", "article_author", "image")

    def __init__(self, *args, **kwargs):
        super(CMSOpenGraphForm, self).__init__(*args, **kwargs)
        self.fields["og_type"].required = False


class CMSOpenGraphFormPart(FormPart):
    priority = 20
    name = "opengraph"
    form = CMSOpenGraphForm

    def get_form_defs(self):
        if self.object.pk:
            instance = PageOpenGraph.objects.get_or_create(page=self.object)[0]
        else:
            instance = PageOpenGraph(page=self.object)

        yield TemplatedFormDef(
            name=self.name,
            form_class=self.form,
            template_name="shuup/simple_cms/admin/_edit_og_form.jinja",
            required=True,
            kwargs={
                "instance": instance,
                "languages": settings.LANGUAGES
            }
        )

    def form_valid(self, form):
        form[self.name].instance.page = self.object
        form[self.name].save()
