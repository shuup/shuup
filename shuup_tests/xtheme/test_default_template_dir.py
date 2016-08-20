# -*- coding: utf-8 -*-
import pytest

from django.core.urlresolvers import reverse

from shuup.testing.factories import get_default_shop
from shuup.testing.themes import ShuupTestingTheme, ShuupTestingThemeWithCustomBase
from shuup.xtheme.testing import override_current_theme_class
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
def test_theme_without_default_template_dir():
    get_default_shop()
    with override_current_theme_class(ShuupTestingTheme):
        c = SmartClient()
        soup = c.soup(reverse("shuup:index"))
        assert "Simple base for themes to use" not in soup
        assert "Welcome to test Shuup!" in soup.find("div", {"class": "page-content"}).text


@pytest.mark.django_db
def test_theme_with_default_template_dir():
    get_default_shop()
    with override_current_theme_class(ShuupTestingThemeWithCustomBase):
        c = SmartClient()
        soup = c.soup(reverse("shuup:index"))
        assert "Simple base for themes to use" in soup.find("h1").text
        assert "Welcome to test Shuup!" in soup.find("h1").text

