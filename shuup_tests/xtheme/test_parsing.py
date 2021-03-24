# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from jinja2 import TemplateSyntaxError

from shuup.xtheme.parsing import NestingError, NonConstant
from shuup.xtheme.testing import override_current_theme_class
from shuup_tests.xtheme.utils import get_jinja2_engine


def test_parsing():
    with override_current_theme_class(None):
        jeng = get_jinja2_engine()
        template = jeng.get_template("complex.jinja")
        assert template  # it'sa me! template!


def test_nonconstant_placeholder_name_fails():
    with pytest.raises(NonConstant):
        get_jinja2_engine().from_string("""{% placeholder "foo" ~ foo %}{% endplaceholder %}""")


def test_bare_placeholder_name_succeeds():
    get_jinja2_engine().from_string("""{% placeholder foo %}{% endplaceholder %}""")


def test_unplaceheld_cola_fails():
    with pytest.raises(NestingError):
        get_jinja2_engine().from_string("""{% column %}{% endcolumn %}""")


def test_nondict_column_arg_fails():
    with pytest.raises(ValueError):
        get_jinja2_engine().from_string(
            """
        {% placeholder foo %}
        {% column 666 %}{% endcolumn %}
        {% endplaceholder %}
        """
        )


def test_nonconstant_column_arg_fails():
    with pytest.raises(ValueError):
        get_jinja2_engine().from_string(
            """
        {% placeholder foo %}
        {% column {"var": e} %}{% endcolumn %}
        {% endplaceholder %}
        """
        )


def test_argumented_row_fails():
    with pytest.raises(ValueError):
        get_jinja2_engine().from_string(
            """
        {% placeholder foo %}
        {% row {"var": e} %}{% endrow %}
        {% endplaceholder %}
        """
        )


def test_nested_placeholders_fail():
    with pytest.raises(NestingError):
        get_jinja2_engine().from_string(
            """
        {% placeholder foo %}
            {% placeholder bar %}{% endplaceholder %}
        {% endplaceholder %}
        """
        )


def test_nonconstant_plugin_content_fails():
    with pytest.raises(NonConstant):
        get_jinja2_engine().from_string(
            """
        {% placeholder foo %}
            {% plugin "text" %}
            text = {{ volcano }}
            {% endplugin %}
        {% endplaceholder %}
        """
        )


def test_nonstring_but_constant_plugin_content_fails():
    with pytest.raises(NonConstant):
        get_jinja2_engine().from_string(
            """
        {% placeholder foo %}
            {% plugin "text" %}
            text = {{ 8 }}
            {% endplugin %}
        {% endplaceholder %}
        """
        )


@pytest.mark.django_db
def test_placeholder_invalid_parameter():
    with pytest.raises(TemplateSyntaxError):
        get_jinja2_engine().from_string(
            """
        {% placeholder stuff some_invalid_parameter %}
            {% plugin "text" %}
            text = "Some stuff"
            {% endplugin %}
        {% endplaceholder %}
        """
        )


def test_placeholder_accepts_valid_global_parameter():
    get_jinja2_engine().from_string(
        """
    {% placeholder "stuff" global %}
        {% plugin "text" %}
        text = "More stuff"
        {% endplugin %}
    {% endplaceholder %}
    """
    )


def test_placeholder_parameter_quotes_or_no_quotes_okay():
    parameter_markup = """
    {%% placeholder stuff %s %%}
        {%% plugin "text" %%}
        text = "More stuff"
        {%% endplugin %%}
    {%% endplaceholder %%}
    """
    get_jinja2_engine().from_string(parameter_markup % "global")
    get_jinja2_engine().from_string(parameter_markup % '"global"')
