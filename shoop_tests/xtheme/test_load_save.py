# -*- coding: utf-8 -*-
import pytest

from shoop.xtheme import Theme, XTHEME_GLOBAL_VIEW_NAME
from shoop.xtheme.view_config import ViewConfig
from shoop_tests.utils import printable_gibberish


class ATestTheme(Theme):
    identifier = "test"


@pytest.mark.django_db
def test_load_save_default():
    view_name = printable_gibberish()
    theme = ATestTheme()
    vc = ViewConfig(theme=theme, view_name=view_name, draft=True)
    placeholder_name = "test_ph"
    data = {"dummy": True}
    assert not vc.saved_view_config.get_layout_data(placeholder_name)
    assert vc.save_default_placeholder_layout(placeholder_name, data)
    assert not vc.save_default_placeholder_layout(placeholder_name, data)

    # Not in public mode yet, right?
    assert not ViewConfig(theme=theme, view_name=view_name, draft=False).saved_view_config.get_layout_data(placeholder_name)

    # But it is in drafts, even if we reload it?
    vc = ViewConfig(theme=theme, view_name=view_name, draft=True)
    assert vc.saved_view_config.get_layout_data(placeholder_name) == data


@pytest.mark.django_db
def test_load_save_publish():
    view_name = printable_gibberish()
    theme = ATestTheme()
    vc = ViewConfig(theme=theme, view_name=view_name, draft=True)
    placeholder_name = "test_ph"
    data = {"dummy": True}
    vc.save_placeholder_layout(placeholder_name, data)
    assert not ViewConfig(theme=theme, view_name=view_name, draft=False).saved_view_config.get_layout_data(placeholder_name)
    vc.publish()
    with pytest.raises(ValueError):  # Republishment is bad
        vc.publish()
    with pytest.raises(ValueError):  # Editing directly in public is bad
        vc.save_placeholder_layout(placeholder_name, "break all the things")
    with pytest.raises(ValueError):  # Can't quite revert public changes either
        vc.revert()
    assert ViewConfig(theme=theme, view_name=view_name, draft=False).saved_view_config.get_layout_data(placeholder_name)


@pytest.mark.django_db
def test_draft_reversion():
    view_name = printable_gibberish()
    theme = ATestTheme()
    placeholder_name = "test_ph"
    vc = ViewConfig(theme=theme, view_name=view_name, draft=True)
    def get_layout_data(draft):
        # shorthand -- we're going to be doing this a lot in this test case
        return ViewConfig(theme=theme, view_name=view_name, draft=draft).saved_view_config.get_layout_data(placeholder_name)
    data1 = {printable_gibberish(): True}
    data2 = {printable_gibberish(): True}
    vc.save_placeholder_layout(placeholder_name, data1)
    vc.publish()

    assert get_layout_data(draft=False) == data1
    assert get_layout_data(draft=True) == data1
    vc = ViewConfig(theme=theme, view_name=view_name, draft=True)
    svc = vc.saved_view_config
    assert svc.draft
    assert svc.get_layout_data(placeholder_name) == data1
    # Make changes over the last published version
    svc.set_layout_data(placeholder_name, data2)
    svc.save()
    # Still all good in public?
    assert get_layout_data(draft=False) == data1
    # Still got it in draft?
    assert get_layout_data(draft=True) == data2
    # Actually revert those draft changes now!
    vc.revert()
    # So in draft we're back to the published version, right?
    assert get_layout_data(draft=True) == data1


def test_unthemebound_view_config_cant_do_much():
    vc = ViewConfig(theme=None, view_name="durr", draft=True)
    with pytest.raises(ValueError):
        vc.publish()
    with pytest.raises(ValueError):
        vc.revert()
    with pytest.raises(ValueError):
        vc.save_placeholder_layout("hurr", {"foo": True})
    l = vc.get_placeholder_layout("hurr")  # loading should work, but . . .
    assert not len(l.rows)  # . . . there shouldn't be much in there


@pytest.mark.django_db
def test_unsaved_vc_reversion():
    vc = ViewConfig(theme=ATestTheme(), view_name=printable_gibberish(), draft=True)
    vc.revert()  # No-op, since this has never been saved (but shouldn't crash either)
