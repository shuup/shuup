"""
Sphinx Shoop theme.

This theme is a fork of Sphinx ReadTheDocs theme from
https://github.com/snide/sphinx_rtd_theme/.
"""
import os

__version__ = "0.6.0"
__version_full__ = __version__

VERSION = tuple(int(x) for x in __version__.split("."))


def get_html_theme_path():
    """Return list of HTML theme paths."""
    cur_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    return cur_dir
