# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import VERSION

from shuup.testing.models import PseudoPaymentProcessor
from shuup.utils.analog import BaseLogEntry, define_log_model


def test_analog():
    PseudoPaymentProcessorLogEntry = define_log_model(PseudoPaymentProcessor)
    assert PseudoPaymentProcessorLogEntry.__module__ == PseudoPaymentProcessor.__module__

    related_field_name = "rel"
    relation_manager = getattr(PseudoPaymentProcessorLogEntry._meta.get_field("target"), "remote_field")
    assert relation_manager.model is PseudoPaymentProcessor

    relation_manager = getattr(PseudoPaymentProcessor.log_entries, "rel")
    assert relation_manager.model is PseudoPaymentProcessor
    assert relation_manager.related_model is PseudoPaymentProcessorLogEntry

    assert issubclass(PseudoPaymentProcessorLogEntry, BaseLogEntry)
    assert isinstance(PseudoPaymentProcessorLogEntry(), BaseLogEntry)
