# -*- coding: utf-8 -*-
from shoop.xtheme.editing import could_edit, is_edit_mode, set_edit_mode
from shoop_tests.utils.faux_users import SuperUser


def test_edit_priv(rf):
    request = rf.get("/")
    request.user = SuperUser()
    request.session = {}
    assert could_edit(request)
    assert not is_edit_mode(request)
    set_edit_mode(request, True)
    assert is_edit_mode(request)
    set_edit_mode(request, False)
    assert not is_edit_mode(request)
