# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.apps.provides import override_provides
from shuup.testing import factories
from shuup.utils.django_compat import reverse
from shuup.xtheme import get_current_theme
from shuup.xtheme.layout import (
    AnonymousContactLayout,
    CategoryLayout,
    CompanyContactLayout,
    ContactLayout,
    Layout,
    PersonContactLayout,
    ProductLayout,
)
from shuup.xtheme.layout.utils import get_layout_data_key
from shuup.xtheme.view_config import ViewConfig
from shuup_tests.utils import SmartClient, printable_gibberish
from shuup_tests.xtheme.utils import get_request


@pytest.mark.django_db
def test_get_placeholder_layouts():
    vc = _get_basic_view_config()
    product = factories.create_product("test", name="Test product name")
    category = factories.get_default_category()

    placeholder_name = "hermit"
    context = {"request": get_request(), "product": product, "category": category}

    provides = []
    with override_provides("xtheme_layout", provides):
        assert len(vc.get_placeholder_layouts(context, placeholder_name)) == 1  # Default layout

    provides.append("shuup.xtheme.layout.ProductLayout")
    with override_provides("xtheme_layout", provides):
        assert len(vc.get_placeholder_layouts(context, placeholder_name)) == 2

    provides.append("shuup.xtheme.layout.CategoryLayout")
    with override_provides("xtheme_layout", provides):
        assert len(vc.get_placeholder_layouts(context, placeholder_name)) == 3

    provides.append("shuup.xtheme.layout.AnonymousContactLayout")
    with override_provides("xtheme_layout", provides):
        assert len(vc.get_placeholder_layouts(context, placeholder_name)) == 4


@pytest.mark.django_db
def test_default_layout():
    vc = _get_basic_view_config()
    product = factories.create_product("test", name="Test product name")
    category = factories.get_default_category()

    placeholder_name = "wildhorse"
    context = {"request": get_request(), "product": product, "category": category}
    layout = vc.get_placeholder_layout(Layout, placeholder_name)
    assert isinstance(layout, Layout)
    assert layout.get_help_text({}) == layout.get_help_text(context)

    _add_plugin_and_test_save(vc, layout, placeholder_name, context)


@pytest.mark.django_db
def test_product_layout():
    vc = _get_basic_view_config()
    product = factories.create_product("test", shop=factories.get_default_shop(), name="Test product name")

    placeholder_name = "wow"
    # Context doesn't validate with the product layout
    assert vc.get_placeholder_layout(ProductLayout, placeholder_name) is None

    context = {"product": product}
    layout = vc.get_placeholder_layout(ProductLayout, placeholder_name, context=context)
    assert isinstance(layout, ProductLayout)
    assert layout.get_help_text({}) == ""  # Invalid context for help text
    assert product.name in layout.get_help_text(context)
    _assert_empty_layout(layout, placeholder_name)

    _add_plugin_and_test_save(vc, layout, placeholder_name, context)

    # Make sure layout only available for this one product
    new_product = factories.create_product("new_test")
    context = {"product": new_product}
    layout = vc.get_placeholder_layout(ProductLayout, placeholder_name, context=context)
    _assert_empty_layout(layout, placeholder_name)


@pytest.mark.django_db
def test_product_detail_view():
    vc = _get_basic_view_config(view_name="ProductDetailView")
    product = factories.create_product("test", shop=factories.get_default_shop(), name="Test product name")
    product2 = factories.create_product("test2", shop=factories.get_default_shop(), name="Test product name 2")
    placeholder_name = "product_extra_1"
    context = {"product": product}
    layout = vc.get_placeholder_layout(ProductLayout, placeholder_name, context=context)
    plugin_text = printable_gibberish()
    _add_plugin_and_test_save(vc, layout, placeholder_name, context, plugin_text)

    # Also let's confirm that the plugin visibility works with smart client
    c = SmartClient()
    soup = c.soup(reverse("shuup:product", kwargs={"pk": product.id, "slug": product.slug}))
    product_details = soup.find("div", {"class": "product-basic-details"})
    assert plugin_text in product_details.text

    c = SmartClient()
    soup = c.soup(reverse("shuup:product", kwargs={"pk": product2.id, "slug": product2.slug}))
    product_details = soup.find("div", {"class": "product-basic-details"})
    assert plugin_text not in product_details.text


@pytest.mark.django_db
def test_category_layout():
    vc = _get_basic_view_config()
    category = factories.get_default_category()

    placeholder_name = "japanese"
    context = {"category": category}
    layout = vc.get_placeholder_layout(CategoryLayout, placeholder_name, context=context)
    assert isinstance(layout, CategoryLayout)
    assert layout.get_help_text({}) == ""  # Invalid context for help text
    assert category.name in layout.get_help_text(context)
    _assert_empty_layout(layout, placeholder_name)

    _add_plugin_and_test_save(vc, layout, placeholder_name, context)


@pytest.mark.django_db
def test_anon_layout():
    vc = _get_basic_view_config()

    placeholder_name = "hip hop"
    context = {"request": get_request()}  # By default user is anonymous
    layout = vc.get_placeholder_layout(AnonymousContactLayout, placeholder_name, context=context)
    assert isinstance(layout, AnonymousContactLayout)
    help_text = layout.get_help_text({})  # Same help text with or without the context
    assert layout.get_help_text(context) == help_text

    # Invalid contexts for rest of the contact group layouts
    assert vc.get_placeholder_layout(ContactLayout, placeholder_name, context=context) is None
    assert vc.get_placeholder_layout(PersonContactLayout, placeholder_name, context=context) is None
    assert vc.get_placeholder_layout(CompanyContactLayout, placeholder_name, context=context) is None

    _add_plugin_and_test_save(vc, layout, placeholder_name, context)


@pytest.mark.django_db
def test_contact_layout():
    vc = _get_basic_view_config()
    person = factories.create_random_person()

    placeholder_name = "country"
    request = get_request()
    request.customer = person
    context = {"request": request}
    layout = vc.get_placeholder_layout(ContactLayout, placeholder_name, context=context)
    assert isinstance(layout, ContactLayout)
    help_text = layout.get_help_text({})  # Same help text with or without the context
    assert layout.get_help_text(context) == help_text

    # Invalid context for anon and company layouts
    assert vc.get_placeholder_layout(AnonymousContactLayout, placeholder_name, context=context) is None
    assert vc.get_placeholder_layout(CompanyContactLayout, placeholder_name, context=context) is None

    # Valid contexts for anon and person contact layout
    assert vc.get_placeholder_layout(PersonContactLayout, placeholder_name, context=context) is not None

    _add_plugin_and_test_save(vc, layout, placeholder_name, context)

    # Ok here we want to check that the plugin doesn't end up to the
    # person contact placeholders
    person_layout = vc.get_placeholder_layout(PersonContactLayout, placeholder_name, context=context)
    _assert_empty_layout(person_layout, placeholder_name)


@pytest.mark.django_db
def test_person_contact_layout():
    vc = _get_basic_view_config()
    person = factories.create_random_person()

    placeholder_name = "kissa"
    request = get_request()
    request.customer = person
    context = {"request": request}
    layout = vc.get_placeholder_layout(PersonContactLayout, placeholder_name, context=context)
    assert isinstance(layout, PersonContactLayout)
    help_text = layout.get_help_text({})  # Same help text with or without the context
    assert layout.get_help_text(context) == help_text

    # Invalid contexts for anon and company layouts
    assert vc.get_placeholder_layout(AnonymousContactLayout, placeholder_name, context=context) is None
    assert vc.get_placeholder_layout(CompanyContactLayout, placeholder_name, context=context) is None

    # Valid contexts for contact layout
    assert vc.get_placeholder_layout(ContactLayout, placeholder_name, context=context) is not None

    _add_plugin_and_test_save(vc, layout, placeholder_name, context)

    # Ok here we want to check that the plugin doesn't end up to the
    # contact placeholders
    contact_layout = vc.get_placeholder_layout(ContactLayout, placeholder_name, context=context)
    _assert_empty_layout(contact_layout, placeholder_name)


@pytest.mark.django_db
def test_company_contact_layout():
    vc = _get_basic_view_config()
    company = factories.create_random_company()

    placeholder_name = "kissa"
    request = get_request()
    request.customer = company
    context = {"request": request}
    layout = vc.get_placeholder_layout(CompanyContactLayout, placeholder_name, context=context)
    assert isinstance(layout, CompanyContactLayout)
    help_text = layout.get_help_text({})  # Same help text with or without the context
    assert layout.get_help_text(context) == help_text

    # Invalid contexts for anon and person contact layouts
    assert vc.get_placeholder_layout(AnonymousContactLayout, placeholder_name, context=context) is None
    assert vc.get_placeholder_layout(PersonContactLayout, placeholder_name, context=context) is None

    # Valid contexts for contact layout
    assert vc.get_placeholder_layout(ContactLayout, placeholder_name, context=context) is not None

    _add_plugin_and_test_save(vc, layout, placeholder_name, context)

    # Ok here we want to check that the plugin doesn't end up to the
    # contact placeholders
    contact_layout = vc.get_placeholder_layout(ContactLayout, placeholder_name, context=context)
    _assert_empty_layout(contact_layout, placeholder_name)


@pytest.mark.django_db
def test_index_view_with_contact_limitatons():
    shop = factories.get_default_shop()
    password = "kissa123"

    # Person 1 to test contact and person contact layouts
    person1 = factories.create_random_person(shop=shop)
    person1.user = factories.create_random_user()
    person1.user.set_password(password)
    person1.user.save()
    person1.save()

    # Person 2 to test company layout
    person2 = factories.create_random_person(shop=shop)
    person2.user = factories.create_random_user()
    person2.user.set_password(password)
    person2.user.save()
    person2.save()
    company = factories.create_random_company(shop=shop)
    company.members.add(person2)

    placeholder_name = "front_content"
    request = get_request()
    context = {"request": request}

    # Add plugin for anons
    vc = _get_basic_view_config(view_name="IndexView")
    anon_plugin_text = "This content is only for guests"
    layout = vc.get_placeholder_layout(AnonymousContactLayout, placeholder_name, context=context)
    _add_plugin_and_test_save(vc, layout, placeholder_name, context, anon_plugin_text)

    # Add plugin for contact
    vc = _get_basic_view_config(view_name="IndexView")
    context["request"].customer = person1
    contact_plugin_text = "This content is only for users logged in"
    layout = vc.get_placeholder_layout(ContactLayout, placeholder_name, context=context)
    _add_plugin_and_test_save(vc, layout, placeholder_name, context, contact_plugin_text)

    # Add plugin for person contacts
    vc = _get_basic_view_config(view_name="IndexView")
    person_contact_plugin_text = "This content is only for person contacts"
    layout = vc.get_placeholder_layout(PersonContactLayout, placeholder_name, context=context)
    _add_plugin_and_test_save(vc, layout, placeholder_name, context, person_contact_plugin_text)

    # Add plugin for companies
    vc = _get_basic_view_config(view_name="IndexView")
    context["request"].customer = company
    company_plugin_text = "This content is only for companies"
    layout = vc.get_placeholder_layout(CompanyContactLayout, placeholder_name, context=context)
    _add_plugin_and_test_save(vc, layout, placeholder_name, context, company_plugin_text)

    c = SmartClient()  # By default there is no user logged in
    soup = c.soup(reverse("shuup:index"))
    page_content = soup.find("div", {"class": "page-content"})
    page_content_text = page_content.text
    assert anon_plugin_text in page_content_text
    assert contact_plugin_text not in page_content_text
    assert person_contact_plugin_text not in page_content_text
    assert company_plugin_text not in page_content_text

    # Login as person1 user
    c = SmartClient()
    c.login(username=person1.user.username, password=password)
    soup = c.soup(reverse("shuup:index"))
    page_content = soup.find("div", {"class": "page-content"})
    page_content_text = page_content.text
    assert anon_plugin_text not in page_content_text
    assert contact_plugin_text in page_content_text
    assert person_contact_plugin_text in page_content_text
    assert company_plugin_text not in page_content_text

    # Login as person2 user which is linked to company
    c = SmartClient()
    c.login(username=person2.user.username, password=password)
    soup = c.soup(reverse("shuup:index"))
    page_content = soup.find("div", {"class": "page-content"})
    page_content_text = page_content.text
    assert anon_plugin_text not in page_content_text
    assert contact_plugin_text in page_content_text
    assert person_contact_plugin_text not in page_content_text
    assert company_plugin_text in page_content_text


def _get_basic_view_config(view_name="pow"):
    shop = factories.get_default_shop()
    theme = get_current_theme(shop)
    return ViewConfig(theme=theme, shop=shop, view_name=view_name, draft=True)


def _add_plugin_and_test_save(view_config, layout, placeholder_name, context, plugin_text=None):
    if not plugin_text:
        plugin_text = printable_gibberish()
    _add_basic_plugin(layout, plugin_text)
    view_config.save_placeholder_layout(get_layout_data_key(placeholder_name, layout, context), layout)
    view_config.publish()

    # Now refetching the layout we should get the plugin
    layout = view_config.get_placeholder_layout(layout.__class__, placeholder_name, context=context)
    assert isinstance(layout, layout.__class__)
    _assert_layout_content_for_basic_plugin(layout, placeholder_name, plugin_text)


def _add_basic_plugin(layout, plugin_text):
    layout.begin_column({"md": 8})
    layout.add_plugin("text", {"text": plugin_text})


def _assert_layout_content_for_basic_plugin(layout, placeholder_name, plugin_text):
    serialized = layout.serialize()
    expected = {
        "name": placeholder_name,
        "rows": [{"cells": [{"config": {"text": plugin_text}, "plugin": "text", "sizes": {"md": 8}}]}],
    }
    assert bool(serialized == expected)


def _assert_empty_layout(layout, placeholder_name):
    serialized = layout.serialize()
    assert len(serialized["rows"]) == 0
    assert serialized["name"] == placeholder_name
