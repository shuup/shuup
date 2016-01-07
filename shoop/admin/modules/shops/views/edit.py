# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shoop.admin.forms.widgets import MediaChoiceWidget
from shoop.admin.toolbar import get_default_edit_toolbar
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import Shop
from shoop.core.utils.form_mixins import ProtectedFieldsMixin
from shoop.utils.excs import Problem
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class ShopForm(ProtectedFieldsMixin, MultiLanguageModelForm):
    change_protect_field_text = _("This field cannot be changed since there are existing orders for this shop.")

    class Meta:
        model = Shop
        exclude = ("owner", "options")

    def __init__(self, **kwargs):
        super(ShopForm, self).__init__(**kwargs)
        self.fields["logo"].widget = MediaChoiceWidget(clearable=True)


class ShopEditView(CreateOrUpdateView):
    model = Shop
    form_class = ShopForm
    template_name = "shoop/admin/shops/edit.jinja"
    context_object_name = "shop"
    add_form_errors_as_messages = True

    def get_object(self, queryset=None):
        obj = super(ShopEditView, self).get_object(queryset)
        if not settings.SHOOP_ENABLE_MULTIPLE_SHOPS:
            if not obj.pk and Shop.objects.count() >= 1:
                # This seems like a new object, but there already is (at least) one shop...
                raise Problem(_(u"Only one shop permitted."))

        return obj

    def get_toolbar(self):
        save_form_id = self.get_save_form_id()
        return get_default_edit_toolbar(self, save_form_id, with_split_save=settings.SHOOP_ENABLE_MULTIPLE_SHOPS)
