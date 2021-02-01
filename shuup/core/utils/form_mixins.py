# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import ugettext_lazy as _


class ProtectedFieldsMixin(object):
    change_protect_field_text = _("This field cannot be changed since it is protected.")

    def _get_protected_fields(self):
        """
        Get a tuple of protected fields if set.
        The fields are set in model level when model has `ChangeProtected`
        """
        if self.instance and self.instance.pk:
            are_changes_protected = getattr(self.instance, "_are_changes_protected", None)
            if are_changes_protected:  # Supports the `_are_changes_protected` protocol?
                if not are_changes_protected():  # Not protected though?
                    return ()  # Nothing protected, then.
            return getattr(self.instance, "protected_fields", ())
        return ()

    def disable_protected_fields(self):
        for field in self._get_protected_fields():
            self.fields[field].widget.attrs["disabled"] = True
            self.fields[field].help_text = self.change_protect_field_text
            self.fields[field].required = False

    def clean_protected_fields(self, cleaned_data):
        """
        Ignore protected fields (they are set to `disabled`,
        so they will not be in the form data).

        As a side effect, this removes the fields from `changed_data` too.

        :param cleaned_data: Cleaned data
        :type cleaned_data: dict
        :return: Cleaned data without protected field data
        :rtype: dict
        """
        for field in self._get_protected_fields():
            if field in self.changed_data:
                self.changed_data.remove(field)
            cleaned_data[field] = getattr(self.instance, field)
        return cleaned_data

    def clean(self):
        return self.clean_protected_fields(super(ProtectedFieldsMixin, self).clean())

    def __init__(self, **kwargs):
        super(ProtectedFieldsMixin, self).__init__(**kwargs)
        self.disable_protected_fields()
