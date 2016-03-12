# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db.transaction import atomic

from shoop.admin.form_part import (
    FormPart, FormPartsViewMixin, SaveFormPartsMixin, TemplatedFormDef
)
from shoop.admin.toolbar import get_default_edit_toolbar
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.social_media.models import SocialMediaLink

from .forms import SocialMediaLinkForm


class SocialMediaLinkFormPart(FormPart):
    priority = 1
    name = "base"
    form = SocialMediaLinkForm

    def get_form_defs(self):
        yield TemplatedFormDef(
            self.name,
            self.form,
            template_name="shoop/admin/social_media/_edit_base_form.jinja",
            required=True,
            kwargs={
                "instance": self.object,
            }
        )

    def form_valid(self, form):
        self.object = form[self.name].save()
        return self.object


class SocialMediaLinkEditView(FormPartsViewMixin, SaveFormPartsMixin, CreateOrUpdateView):
    model = SocialMediaLink
    template_name = "shoop/admin/social_media/edit.jinja"
    base_form_part_classes = [
        SocialMediaLinkFormPart,
    ]
    context_object_name = "social_media_link"
    form_part_class_provide_key = "admin_social_media_form_part"

    def get_toolbar(self):
        save_form_id = self.get_save_form_id()
        if save_form_id:
            return get_default_edit_toolbar(self, save_form_id, delete_url="shoop_admin:social_media_link.delete")

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)
