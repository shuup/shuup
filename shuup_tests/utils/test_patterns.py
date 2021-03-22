# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.utils.patterns import Pattern, _compile_pattern, pattern_matches


def ReconstitutedPattern(pat):
    return Pattern(Pattern(pat).as_normalized())


@pytest.mark.parametrize("ctor", (Pattern, ReconstitutedPattern))
def test_empty_pat(ctor):
    empty_pat = ctor("")
    assert not empty_pat.matches("10")
    assert not empty_pat.matches("20")
    assert not empty_pat.matches("")


@pytest.mark.parametrize("ctor", (Pattern, ReconstitutedPattern))
def test_all_pat(ctor):
    all_pat = ctor("*")
    assert all_pat.matches("10")
    assert all_pat.matches("20")
    assert all_pat.matches("30")
    assert all_pat.matches("40")
    assert all_pat.matches("50")
    assert all_pat.matches("60")


@pytest.mark.parametrize("ctor", (Pattern, ReconstitutedPattern))
def test_all_except_pat(ctor):
    a_e_pat = ctor("*,!30")
    assert a_e_pat.matches("10")
    assert a_e_pat.matches("20")
    assert not a_e_pat.matches("30")
    assert a_e_pat.matches("40")
    assert a_e_pat.matches("50")
    assert a_e_pat.matches("60")


@pytest.mark.parametrize("ctor", (Pattern, ReconstitutedPattern))
def test_distinct_pat(ctor):
    distinct_pat = ctor("10,20,30,40")
    assert not distinct_pat.matches("5")
    assert distinct_pat.matches("10")
    assert distinct_pat.matches("20")
    assert distinct_pat.matches("30")
    assert distinct_pat.matches("40")
    assert not distinct_pat.matches("50")


@pytest.mark.parametrize("ctor", (Pattern, ReconstitutedPattern))
def test_distinct_pat_with_negation(ctor):
    distinct_pat = ctor("10,20,30,40,!40")
    assert not distinct_pat.matches("5")
    assert distinct_pat.matches("10")
    assert distinct_pat.matches("20")
    assert distinct_pat.matches("30")
    assert not distinct_pat.matches("40")
    assert not distinct_pat.matches("50")


@pytest.mark.parametrize("ctor", (Pattern, ReconstitutedPattern))
def test_range_pat(ctor):
    range_pat = ctor("b-jz,40")
    assert not range_pat.matches("a")
    assert range_pat.matches("ca")
    assert range_pat.matches("fe")
    assert range_pat.matches("40")
    assert not range_pat.matches("qq")
    assert not range_pat.matches("50")


@pytest.mark.parametrize("ctor", (Pattern, ReconstitutedPattern))
def test_range_pat_with_negation(ctor):
    range_pat = ctor("10-30,!20,40")
    assert not range_pat.matches("5")
    assert range_pat.matches("10")
    assert not range_pat.matches("20")
    assert range_pat.matches("30")
    assert not range_pat.matches("35")
    assert range_pat.matches("40")
    assert not range_pat.matches("50")


@pytest.mark.parametrize("ctor", (Pattern, ReconstitutedPattern))
def test_wildcards(ctor):
    wc_pat = ctor("1*,!11*")
    assert wc_pat.matches("1000")
    assert not wc_pat.matches("1100")


@pytest.mark.parametrize("ctor", (Pattern, ReconstitutedPattern))
def test_num_match(ctor):
    num_pat = ctor("1-100")
    assert num_pat.matches(93)
    assert not num_pat.matches(930)


@pytest.mark.parametrize("ctor", (Pattern, ReconstitutedPattern))
def test_num_and_alphabetic_matches(ctor):
    num_pat = ctor("100-2000")
    assert num_pat.matches(19), "Matches alphabetically"
    assert num_pat.matches(300), "Matches numerically"


def test_pattern_cache():
    convoluted_pat_text = ",".join([str(x) for x in range(0, 1000, 2)])
    _compile_pattern.cache_clear()
    assert _compile_pattern.cache_info().currsize == 0
    assert pattern_matches(convoluted_pat_text, "32")
    assert _compile_pattern.cache_info().currsize == 1
    assert _compile_pattern.cache_info().misses == 1
    assert not pattern_matches(convoluted_pat_text, "31")
    assert _compile_pattern.cache_info().currsize == 1
    assert _compile_pattern.cache_info().misses == 1
    assert _compile_pattern.cache_info().hits == 1
