# -*- coding: utf-8 -*-
import pytest
from shoop.utils.excs import Problem
from shoop.xtheme.editing import is_edit_mode
from shoop.xtheme.views import xtheme_dispatch
from shoop_tests.utils.faux_users import SuperUser



def test_edit_can_be_set_via_view(rf):
    request = rf.get("/")
    request.user = SuperUser()
    request.session = {}
    request.POST = {"command": "edit_on"}
    xtheme_dispatch(request)
    assert is_edit_mode(request)
    request.POST = {"command": "edit_off"}
    xtheme_dispatch(request)
    assert not is_edit_mode(request)


def test_dispatch_view_kvetches_at_unknown_commands(rf):
    with pytest.raises(Problem):
        xtheme_dispatch(rf.post("/"))

