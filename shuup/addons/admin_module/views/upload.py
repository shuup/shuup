# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import os
import shutil
import tempfile
import traceback
import zipfile
from django import forms
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from shuup.addons.installer import PackageInstaller
from shuup.admin.toolbar import PostActionButton, Toolbar
from shuup.admin.utils.urls import manipulate_query_string
from shuup.utils.django_compat import reverse
from shuup.utils.excs import Problem
from shuup.utils.iterables import first


class AddonUploadForm(forms.Form):
    file = forms.FileField(label=_("Addon file (ZIP)"), help_text=_("Only upload the addon files you trust."))


class AddonUploadView(FormView):
    form_class = AddonUploadForm
    template_name = "shuup/admin/addons/upload.jinja"
    title = "Upload Addon"

    def form_valid(self, form):
        file = form.cleaned_data["file"]
        if not file.name.lower().endswith(".whl"):
            raise Problem(_("Only wheel files (`.whl`) are supported."))
        # TODO: Maybe verify the file before saving?
        tmp_dir = tempfile.mkdtemp(prefix="shuup")
        tmp_token = os.path.basename(tmp_dir)
        filename = os.path.basename(file.name)
        with open(os.path.join(tmp_dir, filename), "wb") as outf:
            shutil.copyfileobj(file, outf)
        return HttpResponseRedirect(
            manipulate_query_string(reverse("shuup_admin:addon.upload_confirm"), file=filename, token=tmp_token)
        )

    def get_context_data(self, **kwargs):
        context = super(AddonUploadView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar(
            [
                PostActionButton(
                    icon="fa fa-upload",
                    form_id="upload_form",
                    text=_("Upload"),
                    extra_css_class="btn-success",
                )
            ],
            view=self,
        )
        return context


class AddonUploadConfirmView(FormView):
    form_class = forms.Form
    template_name = "shuup/admin/addons/upload_confirm.jinja"
    title = "Upload Addon"

    def get_addon_path(self):
        # get filename from GET since this is a view we get redirected in
        filename = os.path.basename(self.request.GET.get("file"))
        tmp_token = self.request.GET.get("token")
        path = os.path.join(tempfile.gettempdir(), tmp_token, filename)
        if not os.path.isfile(path):
            raise ValueError("Error! File not found.")
        if hasattr(os, "geteuid") and os.stat(path).st_uid != os.geteuid():
            raise ValueError("Error! The file is not owned by the current user.")
        return path

    def get_context_data(self, **kwargs):
        context = super(AddonUploadConfirmView, self).get_context_data(**kwargs)

        with zipfile.ZipFile(self.get_addon_path()) as zf:
            context["filenames"] = sorted(zf.namelist())
            pkg_info_path = first(filename for filename in context["filenames"] if filename.endswith("PKG-INFO"))
            if pkg_info_path:
                context["pkg_info"] = zf.read(pkg_info_path).decode("UTF-8", "replace")

        context["toolbar"] = Toolbar(
            [
                PostActionButton(
                    icon="fa fa-download",
                    form_id="install_form",
                    text=_("Install Addon"),
                    extra_css_class="btn-success",
                )
            ],
            view=self,
        )
        return context

    def form_valid(self, form):
        installer = PackageInstaller()
        self.template_name = "shuup/admin/addons/upload_complete.jinja"
        context = {}
        try:
            addon_path = self.get_addon_path()
            installer.install_package(addon_path)
        except Exception:
            context["error"] = traceback.format_exc()
            context["success"] = False
        else:
            context["success"] = True
            try:  # Try cleaning up behind ourselves
                os.unlink(self.get_addon_path())
            except Exception:
                pass
        context["log_content"] = installer.get_log()
        return self.render_to_response(context)
