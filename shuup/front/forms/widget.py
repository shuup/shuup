# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.forms import HiddenInput, Widget
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from filer.models import File


class PictureDnDUploaderWidget(Widget):
    def __init__(self, attrs=None, kind="images", upload_path="/contacts", clearable=False,
                 browsable=True, upload_url=None, dropzone_attrs={}):
        self.kind = kind
        self.upload_path = upload_path
        self.clearable = clearable
        self.dropzone_attrs = dropzone_attrs

        super(PictureDnDUploaderWidget, self).__init__(attrs)

    def _get_file_attrs(self, file):
        if not file:
            return []
        try:
            thumbnail = file.easy_thumbnails_thumbnailer.get_thumbnail({
                'size': (120, 120),
                'crop': True,
                'upscale': True,
                'subject_location': file.subject_location
            })
        except Exception:
            thumbnail = None
        data = {
            "id": file.id,
            "name": file.label,
            "size": file.size,
            "url": file.url,
            "thumbnail": (thumbnail.url if thumbnail else None),
            "date": file.uploaded_at.isoformat()
        }
        return ["data-%s='%s'" % (key, val) for key, val in six.iteritems(data) if val is not None]

    def render(self, name, value, attrs={}, renderer=None):
        pk_input = HiddenInput().render(name, value, attrs)
        file_attrs = [
            "data-upload_path='%s'" % self.upload_path,
            "data-add_remove_links='%s'" % self.clearable,
            "data-dropzone='true'"
        ]
        if self.kind:
            file_attrs.append("data-kind='%s'" % self.kind)

        if self.dropzone_attrs:
            # attributes passed here will be converted into keys with dz_ prefix
            # `{max-filesize: 1}` will be converted into `data-dz_max-filesize="1"`
            file_attrs.extend([
                'data-dz_{}="{}"'.format(k, force_text(v))
                for k, v in self.dropzone_attrs.items()
            ])

        if value:
            file = File.objects.filter(pk=value).first()
            file_attrs += self._get_file_attrs(file)
        return (
            mark_safe("<div id='%s-dropzone' class='dropzone %s' %s>%s</div>" % (
                attrs.get("id", "dropzone"),
                "has-file" if value else "",
                " ".join(file_attrs),
                pk_input
            ))
        )
