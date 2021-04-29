# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.core.models import AttributeChoiceOption, AttributeType

from .forms import AttributeChoiceOptionFormSet, AttributeForm


class AttributeBaseFormPart(FormPart):
    priority = 1

    def get_form_defs(self):
        yield TemplatedFormDef(
            "base",
            AttributeForm,
            template_name="shuup/admin/attributes/_edit_base_form.jinja",
            required=True,
            kwargs={
                "instance": self.object,
                "request": self.request,
                "languages": settings.LANGUAGES,
            },
        )

    def form_valid(self, form):
        self.object = form["base"].save()


class AttributeChoiceOptionsFormPart(FormPart):
    name = "choice_options"
    priority = 2
    formset = AttributeChoiceOptionFormSet

    def get_form_defs(self):
        if not self.object.pk or self.object.type != AttributeType.CHOICES:
            return

        yield TemplatedFormDef(
            self.name,
            self.formset,
            template_name="shuup/admin/attributes/_edit_choice_option_form.jinja",
            required=False,
            kwargs={"attribute": self.object, "languages": settings.LANGUAGES, "request": self.request},
        )

    def form_valid(self, form):
        if self.name in form.forms:
            frm = form.forms[self.name]
            frm.save()
        else:
            # make sure to delete attribute options if there is any
            AttributeChoiceOption.objects.filter(attribute=self.object).delete()
