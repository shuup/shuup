# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import absolute_import

from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.translation import ugettext as _

from shuup import configuration
from shuup.core.setting_keys import SHUUP_ALLOWED_UPLOAD_EXTENSIONS
from shuup.utils.filer import file_size_validator


class UploadFileForm(forms.Form):
    file = forms.FileField(
        label=_("Upload File"),
        validators=[
            FileExtensionValidator(allowed_extensions=configuration.get(None, SHUUP_ALLOWED_UPLOAD_EXTENSIONS)),
            file_size_validator,
        ],
    )


class UploadImageForm(forms.Form):
    file = forms.ImageField(label=_("Upload Image"), validators=[file_size_validator])
