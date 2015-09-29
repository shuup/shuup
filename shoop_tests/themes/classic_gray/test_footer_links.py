# -*- coding: utf-8 -*-
from shoop.themes.classic_gray import ClassicGrayTheme


class DatabaseNaiveClassicGrayTheme(ClassicGrayTheme):
    def __init__(self, test_settings):
        self.test_settings = test_settings
        super(DatabaseNaiveClassicGrayTheme, self).__init__()

    def get_setting(self, key, default=None):
        return self.test_settings.get(key, default)


def test_footer_links():
    cgt = DatabaseNaiveClassicGrayTheme({
        "footer_links": """
        /page
        page
        //page Super page!
        """
    })

    assert list(cgt.get_footer_links()) == [
        {"url": "/page"},
        {"url": "/page"},
        {"url": "//page", "text": "Super page!"},
    ]
