# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models

from shuup.testing.models import PseudoPaymentProcessor
from shuup.utils.analog import BaseLogEntry, define_log_model


def test_analog():
    PseudoPaymentProcessorLogEntry = define_log_model(PseudoPaymentProcessor)
    assert PseudoPaymentProcessorLogEntry.__module__ == PseudoPaymentProcessor.__module__
    assert PseudoPaymentProcessorLogEntry._meta.get_field("target").rel.to is PseudoPaymentProcessor
    assert PseudoPaymentProcessor.log_entries.rel.model is PseudoPaymentProcessor
    assert PseudoPaymentProcessor.log_entries.rel.related_model is PseudoPaymentProcessorLogEntry
    assert issubclass(PseudoPaymentProcessorLogEntry, BaseLogEntry)
    assert isinstance(PseudoPaymentProcessorLogEntry(), BaseLogEntry)
