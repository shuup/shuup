# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.utils.name_mixin import NameMixin


class Ahnuld(NameMixin):
    def __init__(self, first_name, last_name="", prefix="", suffix=""):
        self.first_name_str = first_name
        self.last_name_str = last_name
        self.name = "%s %s" % (first_name, last_name)
        self.prefix = prefix
        self.suffix = suffix

    def get_fullname(self):
        return "%s %s" % (self.first_name_str, self.last_name_str)


def test_basic_name():
    ahnuld = Ahnuld(first_name="Ahnuld", last_name="Strong")
    assert ahnuld.first_name == ahnuld.first_name_str
    assert ahnuld.last_name == ahnuld.last_name_str
    assert ahnuld.full_name == ahnuld.get_fullname()


def test_only_firstname():
    ahnuld = Ahnuld(first_name="Ahnuld")
    assert ahnuld.first_name == ahnuld.first_name_str
    assert ahnuld.last_name == ahnuld.last_name_str
    assert ahnuld.full_name == ahnuld.first_name  # full_name should be first name


def test_prefixes():
    ahnuld = Ahnuld(first_name="Ahnuld", last_name="Strong", prefix="mr.")
    assert ahnuld.first_name == ahnuld.first_name_str
    assert ahnuld.last_name == ahnuld.last_name_str
    assert ahnuld.full_name == ("%s %s" % (ahnuld.prefix, ahnuld.get_fullname()))


def test_prefix_and_suffix():
    ahnuld = Ahnuld(first_name="Ahnuld", last_name="Strong", prefix="mr.", suffix="the oak")
    assert ahnuld.first_name == ahnuld.first_name_str
    assert ahnuld.last_name == ahnuld.last_name_str
    assert ahnuld.full_name == ("%s %s %s" % (ahnuld.prefix, ahnuld.get_fullname(), ahnuld.suffix))


def test_awkward_names():
    ahnuld = Ahnuld(first_name="Ahnuld", last_name="Super Strong in The Sky")
    assert ahnuld.first_name == ahnuld.first_name_str
    assert ahnuld.last_name == ahnuld.last_name_str
    assert ahnuld.full_name == ahnuld.get_fullname()
