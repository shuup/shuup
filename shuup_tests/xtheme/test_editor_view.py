# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from contextlib import contextmanager
from django.contrib.auth.models import AnonymousUser
from django.test.client import RequestFactory

from shuup.apps.provides import override_provides
from shuup.testing.factories import get_default_shop
from shuup.utils.excs import Problem
from shuup.xtheme import XTHEME_GLOBAL_VIEW_NAME
from shuup.xtheme.layout import Layout
from shuup.xtheme.models import SavedViewConfig, SavedViewConfigStatus
from shuup.xtheme.plugins.consts import FALLBACK_LANGUAGE_CODE
from shuup.xtheme.testing import override_current_theme_class
from shuup.xtheme.views.editor import ROW_CELL_LIMIT, EditorView
from shuup_tests.utils import printable_gibberish
from shuup_tests.utils.faux_users import SuperUser
from shuup_tests.utils.forms import get_form_data
from shuup_tests.xtheme.utils import FauxTheme, plugin_override


@contextmanager
def initialize_editor_view(view_name, placeholder_name, request=None):
    if request is None:
        request = RequestFactory().get("/")
    request.shop = get_default_shop()
    request.user = SuperUser()
    if hasattr(request.GET, "_mutable"):
        request.GET._mutable = True  # Ahem
    request.GET.update({"theme": FauxTheme.identifier, "view": view_name, "ph": placeholder_name})

    with plugin_override():
        with override_provides("xtheme", ["shuup_tests.xtheme.utils:FauxTheme"]):
            with override_current_theme_class(FauxTheme):
                yield EditorView(request=request, args=(), kwargs={})


def get_test_layout_and_svc():
    svc = SavedViewConfig(
        theme_identifier=FauxTheme.identifier,
        shop=get_default_shop(),
        view_name=printable_gibberish(),
        status=SavedViewConfigStatus.CURRENT_DRAFT,
    )
    layout = Layout(FauxTheme, "ph")
    layout.add_plugin("text", {"text_*": "hello"})
    svc.set_layout_data(layout.placeholder_name, layout)
    svc.save()
    return layout, svc


@pytest.mark.django_db
def test_anon_cant_edit(rf):
    request = rf.get("/")
    request.user = AnonymousUser()
    request.shop = get_default_shop()
    with pytest.raises(Problem):
        EditorView.as_view()(request)


@pytest.mark.django_db
def test_unknown_theme_fails(rf):
    request = rf.get("/", {"theme": printable_gibberish()})
    request.user = SuperUser()
    request.shop = get_default_shop()
    with pytest.raises(Problem):
        EditorView.as_view()(request)


@pytest.mark.django_db
def test_editor_view_functions():
    layout, svc = get_test_layout_and_svc()

    with initialize_editor_view(svc.view_name, layout.placeholder_name) as view_obj:
        assert isinstance(view_obj, EditorView)
        view_obj.request.GET.update({"x": 0, "y": 0})
        view_obj.dispatch(view_obj.request)
        assert view_obj.current_cell
        assert view_obj.current_cell.serialize() == layout.get_cell(0, 0).serialize()
        # Go through the motions of adding and removing stuff programmatically
        view_obj.dispatch_change_plugin(plugin="text")  # Well it was text to begin with, but...
        assert len(view_obj.layout.rows[0]) == 1
        view_obj.dispatch_add_cell(y=-1)
        assert len(view_obj.layout.rows[0]) == 1
        view_obj.dispatch_add_cell(y=0)
        assert len(view_obj.layout.rows[0]) == 2
        view_obj.dispatch_add_row()
        assert len(view_obj.layout) == 2
        assert len(view_obj.layout.rows[1]) == 1
        view_obj.dispatch_add_cell(y=1)
        assert len(view_obj.layout.rows[1]) == 2
        view_obj.dispatch_del_cell(x=1, y=1)
        assert len(view_obj.layout.rows[1]) == 1
        view_obj.dispatch_del_row(y=1)
        assert len(view_obj.layout) == 1


@pytest.mark.django_db
def test_editor_save(rf):
    layout, svc = get_test_layout_and_svc()

    with initialize_editor_view(svc.view_name, layout.placeholder_name) as view_obj:
        view_obj.request.GET.update({"x": 0, "y": 0})
        view_obj.dispatch(view_obj.request)
        assert view_obj.current_cell
        assert view_obj.form
        assert "general" in view_obj.form.forms
        assert "plugin" in view_obj.form.forms
        form_data = get_form_data(view_obj.form, prepared=True)

        new_text = printable_gibberish()
        form_data["plugin-text_%s" % FALLBACK_LANGUAGE_CODE] = new_text
        form_data["save"] = "1"
        request = rf.post("/pepe/", data=form_data)  # sort of rare pepe
        request.GET = dict(request.GET, x=0, y=0)
        with initialize_editor_view(svc.view_name, layout.placeholder_name, request) as view_obj:
            view_obj.dispatch(request)
            assert view_obj.form
            assert not view_obj.form.errors
            assert view_obj.current_cell.config["text"] == {FALLBACK_LANGUAGE_CODE: new_text}


@pytest.mark.django_db
def test_editor_view_commands():
    with initialize_editor_view(printable_gibberish(), printable_gibberish()) as view_obj:
        view_obj.request.method = "POST"
        view_obj.request.POST = {"command": "add_row"}
        view_obj._populate_vars()  # don't tell anyone we're calling a private method here
        assert len(view_obj.layout) == 0
        view_obj.dispatch(view_obj.request)
        assert len(view_obj.layout) == 1


@pytest.mark.django_db
def test_editor_view_unknown_command():
    with initialize_editor_view(printable_gibberish(), printable_gibberish()) as view_obj:
        view_obj.request.method = "POST"
        view_obj.request.POST = {"command": printable_gibberish()}
        with pytest.raises(Problem):
            view_obj.dispatch(view_obj.request)


@pytest.mark.django_db
def test_editor_cell_limits():
    layout, svc = get_test_layout_and_svc()
    with initialize_editor_view(svc.view_name, layout.placeholder_name) as view_obj:
        view_obj.request.GET.update({"x": 0, "y": 0})
        view_obj.dispatch(view_obj.request)

        for i in range(1, ROW_CELL_LIMIT):
            view_obj.dispatch_add_cell(y=0)

        assert len(view_obj.layout.rows[0]) == ROW_CELL_LIMIT

        with pytest.raises(ValueError):
            view_obj.dispatch_add_cell(y=0)


@pytest.mark.django_db
def test_get_global_placeholder():
    request = RequestFactory().get("/")
    layout, svc = get_test_layout_and_svc()
    with initialize_editor_view(svc.view_name, layout.placeholder_name, request=request) as view_obj:
        view_name_1 = view_obj.dispatch(view_obj.request).context_data["view"].view_config.view_name
        view_obj.request.GET.update({"x": 0, "y": 0, "global_type": True})
        view_name_2 = view_obj.dispatch(view_obj.request).context_data["view"].view_config.view_name
        assert view_name_1 != view_name_2
        assert view_name_2 == XTHEME_GLOBAL_VIEW_NAME
