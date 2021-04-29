# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import unittest
from django.core.exceptions import ValidationError

from shuup.utils.fields import TypedMultipleChoiceWithLimitField


class TypedMultipleChoiceWithLimitFieldTests(unittest.TestCase):
    def setUp(self):
        self.choices = ["a", "b", "c", "d"]
        self.field = TypedMultipleChoiceWithLimitField(
            min_limit=1, max_limit=3, choices=[(i, i) for i in ["a", "b", "c", "d"]]
        )

    def test_min_limit(self):
        value_len_zero = []
        value_len_two = ["a"]
        with pytest.raises(ValidationError):
            self.field.clean(value_len_zero)
        assert self.field.clean(value_len_two) == value_len_two

    def test_max_limit(self):
        value_len_three = ["b", "c", "d"]
        value_len_four = ["a", "b", "c", "d"]
        with pytest.raises(ValidationError):
            self.field.clean(value_len_four)
        assert self.field.clean(value_len_three) == value_len_three
