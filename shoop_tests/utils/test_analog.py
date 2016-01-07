# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models

from shoop.utils.analog import BaseLogEntry, define_log_model


class FakeModel(models.Model):
    pass


def test_analog():
    FakeModelLogEntry = define_log_model(FakeModel)
    assert FakeModelLogEntry.__module__ == FakeModel.__module__
    assert FakeModelLogEntry._meta.get_field("target").rel.to is FakeModel
    assert FakeModel.log_entries.related.model is FakeModel
    assert FakeModel.log_entries.related.related_model is FakeModelLogEntry
    assert issubclass(FakeModelLogEntry, BaseLogEntry)
    assert isinstance(FakeModelLogEntry(), BaseLogEntry)
