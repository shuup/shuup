# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.admin.modules.media.forms import MediaFolderForm


class MediaFolderBaseFormPart(FormPart):
    priority = 1

    def get_form_defs(self):
        yield TemplatedFormDef(
            "media_form",
            MediaFolderForm,
            template_name="shuup/admin/media/edit_folder.jinja",
            required=False,
            kwargs={
                "instance": self.object,
            }
        )

    def form_valid(self, form):
        self.object = form["media_form"].save()
