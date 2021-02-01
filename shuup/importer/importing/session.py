# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.db.models import FieldDoesNotExist, ForeignKey
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatedFieldsModel

from shuup.importer.exceptions import ImporterError


class DataImporterRowSession(object):
    def __init__(self, importer, row, instance, shop):
        self.shop = shop
        self.row = row
        self.importer = importer
        self.instance = instance
        self.deferred_attach = {}
        self.deferred_calls = []
        self.log_messages = []
        self.post_save_objects = []

    def defer(self, key, model, using=None):
        if not using:
            using = {}
        self.deferred_attach[key] = (model, using)

    def defer_call(self, func, *args, **kwargs):
        self.deferred_calls.append(lambda: func(self, *args, **kwargs))

    def get_deferred(self, key):
        return self.deferred_attach.get(key, (None, None))[0]

    def save(self):
        try:
            self.instance._meta.get_field('shop')
            self.instance.shop = self.shop
        except FieldDoesNotExist:
            pass

        try:
            self.instance.save()
        except Exception as e:
            msg = e.message if hasattr(e, "message") else e
            self.importer.other_log_messages.append(_("Row import failed (%s).") % msg)
            raise ImporterError("Error! Row import failed (cannot save).", code="save-failed")

        self._handle_deferred()
        self._handle_postsave_objects()

    def _handle_postsave_objects(self):
        for obj in self.post_save_objects:
            for field in obj._meta.local_fields:
                if isinstance(field, ForeignKey) and isinstance(self.instance, field.rel.to):
                    setattr(obj, field.name, self.instance)
            obj.save()

    def _handle_deferred(self):
        for mkey, (model, using) in sorted(six.iteritems(self.deferred_attach)):
            for key, value in six.iteritems(using):
                setattr(model, key, value)
            if isinstance(model, TranslatedFieldsModel):
                # If the model stored in model.master was not saved when
                # it was set as the master for the model, then it's
                # possible that model.master_id will be None even though
                # model.master.id is not.  That causes parler to crash,
                # so make sure that master_id is set when master.id is.
                if (not model.master_id) and model.master:
                    model.master_id = model.master.pk
            model.save()
        self.deferred_attach.clear()
        while self.deferred_calls:
            self.deferred_calls.pop(0)()

    def log(self, message):
        self.log_messages.append(message)
