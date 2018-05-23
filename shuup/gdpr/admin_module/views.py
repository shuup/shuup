# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from shuup.admin.form_part import FormPartsViewMixin, SaveFormPartsMixin
from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import PostActionButton, Toolbar
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.gdpr.admin_module.forms import (
    GDPRBaseFormPart, GDPRCookieCategoryFormPart
)
from shuup.gdpr.models import GDPRSettings


class GDPRView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = GDPRSettings
    template_name = "shuup/admin/gdpr/edit.jinja"
    base_form_part_classes = [GDPRBaseFormPart, GDPRCookieCategoryFormPart]
    success_url = reverse_lazy("shuup_admin:gdpr")

    def get_toolbar(self):
        toobar = Toolbar([
            PostActionButton(
                icon="fa fa-check-circle",
                form_id="gdpr_form",
                text=_("Save"),
                extra_css_class="btn-success",
            )
        ])
        return toobar

    def get_queryset(self):
        return GDPRSettings.objects.filter(shop=get_shop(self.request))

    def get_object(self):
        return GDPRSettings.get_for_shop(get_shop(self.request))

    def get_context_data(self, **kwargs):
        context = super(GDPRView, self).get_context_data(**kwargs)
        context["title"] = _("General Data Protection Regulation")
        context["toolbar"] = self.get_toolbar()
        return context

    def form_valid(self, form):
        return self.save_form_parts(form)
