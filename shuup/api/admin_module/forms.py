# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup import configuration
from shuup.api import urls as api_urls
from shuup.api.mixins import PermissionHelperMixin
from shuup.api.permissions import (
    DEFAULT_PERMISSION, make_permission_config_key, PermissionLevel
)


class APIPermissionForm(forms.Form):
    API_PERMISSION_CHOICES = (
        (PermissionLevel.DISABLED, _("Disabled")),
        (PermissionLevel.ADMIN, _("Admin Users")),
        (PermissionLevel.AUTHENTICATED_WRITE, _("Authenticated Users - Read/Write")),
        (PermissionLevel.AUTHENTICATED_READ, _("Authenticated Users - Read only")),
        (PermissionLevel.PUBLIC_WRITE, _("Public Users - Read/Write")),
        (PermissionLevel.PUBLIC_READ, _("Public Users - Read only"))
    )

    def __init__(self, **kwargs):
        super(APIPermissionForm, self).__init__(**kwargs)

        # create a choice field for each entry in the router
        # this way it will be easy to set permisions based on each viewset
        # but they must be beautifully configured with name and description
        # to become more presentable to the merchant
        for __, viewset, basename in api_urls.router.registry:
            viewset_instance = viewset()
            field_name = make_permission_config_key(viewset_instance)
            initial = configuration.get(None, field_name, DEFAULT_PERMISSION)

            if issubclass(viewset, PermissionHelperMixin):
                help_text = viewset.get_help_text()
            else:
                help_text = viewset_instance.get_view_description()

            self.fields[field_name] = forms.ChoiceField(label=(viewset_instance.get_view_name() or basename),
                                                        help_text=help_text,
                                                        initial=initial, required=False,
                                                        choices=self.API_PERMISSION_CHOICES)

    def save(self):
        """ Store the fields in configuration """

        if not self.is_valid():
            return

        # that simple, aham
        for field, value in six.iteritems(self.cleaned_data):
            configuration.set(None, field, value)
