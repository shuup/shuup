# -*- coding: utf-8 -*-
import pytest

from shoop.core.models.products import ProductMode
from shoop.utils.enums import map_enum


def test_map_enum_magic_numbers():
    assert map_enum(ProductMode, 0, allow_magic_numbers=True) is ProductMode.NORMAL
    with pytest.raises(ValueError):  # Magic number :(
        map_enum(ProductMode, 0)


def test_map_enum_strings():
    assert map_enum(ProductMode, "normal") is ProductMode.NORMAL
    assert map_enum(ProductMode, "Normal") is ProductMode.NORMAL


def test_map_enum_unknowns():
    assert map_enum(ProductMode, "shower", default=None) is None
    with pytest.raises(ValueError):
        map_enum(ProductMode, "shower")
