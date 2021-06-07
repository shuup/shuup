# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from django.conf import settings
from django.test.client import Client
from django.utils import translation
from filer.models import Image

from shuup.front.apps.carousel.admin_module.forms import SlideForm
from shuup.front.apps.carousel.models import Carousel, LinkTargetType, Slide
from shuup.front.apps.carousel.plugins import BannerBoxPlugin, CarouselPlugin
from shuup.testing.factories import get_default_category, get_default_product, get_default_shop, get_shop
from shuup.testing.utils import apply_request_middleware
from shuup_tests.front.fixtures import get_jinja_context
from shuup_tests.simple_cms.utils import create_page


@pytest.mark.django_db
def test_carousel_plugin_form(rf):
    test_carousel = Carousel.objects.create(name="test")
    plugin = CarouselPlugin(config={})
    form_class = plugin.get_editor_form_class()

    checks = [
        ({}, {"carousel": None, "active": False, "render_image_text": False}),
        ({"carousel": test_carousel.pk}, {"carousel": test_carousel.pk, "active": False, "render_image_text": False}),
        (
            {"carousel": test_carousel.pk, "active": False},
            {"carousel": test_carousel.pk, "active": False, "render_image_text": False},
        ),
        (
            {"carousel": test_carousel.pk, "active": True, "render_image_text": False},
            {"carousel": test_carousel.pk, "active": True, "render_image_text": False},
        ),
        (
            {"carousel": test_carousel.pk, "active": True, "render_image_text": True},
            {"carousel": test_carousel.pk, "active": True, "render_image_text": True},
        ),
    ]

    for data, expected in checks:
        form = form_class(data=data, plugin=plugin, request=apply_request_middleware(rf.get("/")))
        assert form.is_valid()
        assert form.get_config() == expected


@pytest.mark.django_db
def test_carousel_plugin_form_get_context():
    shop = get_default_shop()
    context = get_jinja_context()
    test_carousel = Carousel.objects.create(name="test")
    plugin = CarouselPlugin(config={"carousel": test_carousel.pk})
    assert plugin.get_context_data(context).get("carousel") is None
    test_carousel.shops.add(shop)
    plugin = CarouselPlugin(config={"carousel": test_carousel.pk})
    assert plugin.get_context_data(context).get("carousel") == test_carousel


@pytest.mark.django_db
def test_banner_box_plugin():
    shop = get_default_shop()
    context = get_jinja_context()
    test_carousel = Carousel.objects.create(name="test")
    test_carousel.shops.add(shop)
    plugin = BannerBoxPlugin(config={"carousel": test_carousel.pk, "title": "Test"})
    data = plugin.get_context_data(context)
    assert data.get("carousel") == test_carousel
    assert data.get("title") == "Test"


@pytest.mark.django_db
def test_image_translations():
    test_carousel = Carousel.objects.create(name="test")
    test_image_1 = Image.objects.create(original_filename="slide1.jpg")
    test_image_2 = Image.objects.create(original_filename="slide2.jpg")

    with translation.override("en"):
        test_slide = Slide.objects.create(carousel=test_carousel, name="test", image=test_image_1)
        assert len(test_carousel.slides.all()) == 1
        assert test_slide.get_translated_field("image").original_filename == "slide1.jpg"

    test_slide.set_current_language("fi")
    assert test_slide.get_translated_field("image").original_filename == "slide1.jpg"
    test_slide.image = test_image_2
    test_slide.save()
    assert test_slide.get_translated_field("image").original_filename == "slide2.jpg"

    test_slide.set_current_language("en")
    assert test_slide.get_translated_field("image").original_filename == "slide1.jpg"

    test_slide.set_current_language("jp")
    assert test_slide.get_translated_field("image").original_filename == "slide1.jpg"


@pytest.mark.django_db
def test_slide_links():
    test_carousel = Carousel.objects.create(name="test")
    test_image_1 = Image.objects.create(original_filename="slide1.jpg")
    with translation.override("en"):
        test_slide = Slide.objects.create(carousel=test_carousel, name="test", image=test_image_1)

    # Test external link
    assert len(test_carousel.slides.all()) == 1
    test_link = "http://example.com"
    test_slide.external_link = test_link
    test_slide.save()
    assert test_slide.get_translated_field("external_link") == test_link
    assert test_slide.get_link_url() == test_link

    # Test Product url and link priorities
    test_product = get_default_product()
    test_slide.product_link = test_product
    test_slide.save()
    assert test_slide.get_link_url() == test_link
    test_slide.external_link = None
    test_slide.save()
    assert test_slide.get_link_url().startswith("/p/")  # Close enough...

    # Test Category url and link priorities
    test_category = get_default_category()
    test_slide.category_link = test_category
    test_slide.save()
    assert test_slide.get_link_url().startswith("/p/")  # Close enough...
    test_slide.product_link = None
    test_slide.save()
    assert test_slide.get_link_url().startswith("/c/")  # Close enough...

    # Test CMS page url and link priorities
    attrs = {"url": "test", "shop": get_default_shop()}
    test_page = create_page(**attrs)
    test_slide.cms_page_link = test_page
    test_slide.save()
    assert test_slide.get_link_url().startswith("/c/")  # Close enough...
    test_slide.category_link = None
    test_slide.save()
    assert test_slide.get_link_url().startswith("/test/")

    # Check that external link overrides everything
    test_slide.external_link = test_link
    test_slide.save()
    assert test_slide.get_link_url() == test_link


@pytest.mark.django_db
def test_visible_manager():
    test_dt = datetime(2016, 3, 18, 20, 34, 1, 922791)
    test_carousel = Carousel.objects.create(name="test")
    test_image = Image.objects.create(original_filename="slide.jpg")

    test_slide = Slide.objects.create(carousel=test_carousel, name="test", image=test_image)
    assert not list(test_carousel.slides.visible(dt=test_dt))

    # Available since last week
    test_slide.available_from = test_dt - timedelta(days=7)
    test_slide.save()
    assert len(test_carousel.slides.visible(dt=test_dt)) == 1

    # Available until tomorrow
    test_slide.available_to = test_dt + timedelta(days=1)
    test_slide.save()
    assert len(test_carousel.slides.visible(dt=test_dt)) == 1

    # Expired yesterday
    test_slide.available_to = test_dt - timedelta(days=1)
    test_slide.save()
    assert not list(test_carousel.slides.visible(dt=test_dt))

    # Not available until next week
    test_slide.available_from = test_dt + timedelta(days=7)
    test_slide.available_to = test_dt + timedelta(days=8)
    test_slide.save()
    assert not list(test_carousel.slides.visible(dt=test_dt))


@pytest.mark.django_db
def test_is_visible():
    test_dt = datetime(2016, 3, 18, 20, 34, 1, 922791)
    test_carousel = Carousel.objects.create(name="test")
    test_image = Image.objects.create(original_filename="slide.jpg")
    test_slide = Slide.objects.create(carousel=test_carousel, name="test", image=test_image)
    assert not test_slide.is_visible(dt=test_dt)

    # Available since last week
    test_slide.available_from = test_dt - timedelta(days=7)
    test_slide.save()
    assert test_slide.is_visible(dt=test_dt)

    # Available until tomorrow
    test_slide.available_to = test_dt + timedelta(days=1)
    test_slide.save()
    assert test_slide.is_visible(dt=test_dt)

    # Expired yesterday
    test_slide.available_to = test_dt - timedelta(days=1)
    test_slide.save()
    assert not test_slide.is_visible(dt=test_dt)

    # Not available until next week
    test_slide.available_from = test_dt + timedelta(days=7)
    test_slide.available_to = test_dt + timedelta(days=8)
    test_slide.save()
    assert not test_slide.is_visible(dt=test_dt)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_type,expected_target",
    [
        (LinkTargetType.CURRENT, "_self"),
        (LinkTargetType.NEW, "_blank"),
    ],
)
def test_get_link_target(target_type, expected_target):
    test_carousel = Carousel.objects.create(name="test")
    test_image = Image.objects.create(original_filename="slide.jpg")
    test_slide = Slide.objects.create(carousel=test_carousel, name="test", image=test_image, target=target_type)
    assert test_slide.get_link_target() == expected_target


def test_slide_admin_form(rf, admin_user):
    translation.activate("en")
    shop = get_default_shop()
    category = get_default_category()
    assert category.shops.first() == shop
    page = create_page(**{"url": "test", "shop": shop})
    assert page.shop == shop

    test_carousel = Carousel.objects.create(name="test")
    request = apply_request_middleware(rf.get("/"))
    request.user = admin_user
    request.shop = shop
    slide_form = SlideForm(
        carousel=test_carousel,
        languages=settings.LANGUAGES,
        default_language=settings.PARLER_DEFAULT_LANGUAGE_CODE,
        request=request,
    )

    soup = BeautifulSoup(slide_form.as_table())
    options = soup.find(id="id_category_link").find_all("option")
    assert len(options) == 2
    assert options[0]["value"] == ""
    assert options[1]["value"] == "%s" % category.pk

    options = soup.find(id="id_cms_page_link").find_all("option")
    assert len(options) == 2
    assert options[0]["value"] == ""
    assert options[1]["value"] == "%s" % page.pk

    new_shop = get_shop(identifier="second-shop")
    category.shops.set([new_shop])
    page.shop = new_shop
    page.save()

    slide_form = SlideForm(
        carousel=test_carousel,
        languages=settings.LANGUAGES,
        default_language=settings.PARLER_DEFAULT_LANGUAGE_CODE,
        request=request,
    )

    soup = BeautifulSoup(slide_form.as_table())
    options = soup.find(id="id_category_link").find_all("option")
    assert len(options) == 1
    assert options[0]["value"] == ""

    options = soup.find(id="id_cms_page_link").find_all("option")
    assert len(options) == 1
    assert options[0]["value"] == ""


@pytest.mark.django_db
def test_carousel_custom_colors(rf):
    from shuup.front.apps.carousel.plugins import CarouselPlugin
    from shuup.utils.django_compat import reverse
    from shuup.xtheme._theme import get_current_theme
    from shuup.xtheme.layout import Layout
    from shuup.xtheme.models import SavedViewConfig, SavedViewConfigStatus

    shop = get_default_shop()
    shop.maintenance_mode = False
    shop.save()

    carousel = Carousel.objects.create(name="test")
    carousel.shops.add(shop)
    test_image = Image.objects.create(original_filename="slide.jpg")
    test_slide = Slide.objects.create(
        carousel=carousel,
        name="test",
        available_from=(datetime.now() - timedelta(days=1)),
        image=test_image,
        target=LinkTargetType.CURRENT,
    )

    theme = get_current_theme(shop)

    # adds the carousel to the front page
    layout = Layout(theme, "front_content")
    layout.begin_row()
    layout.begin_column({"md": 12})
    layout.add_plugin(CarouselPlugin.identifier, {"carousel": carousel.pk})
    svc = SavedViewConfig(
        theme_identifier=theme.identifier, shop=shop, view_name="IndexView", status=SavedViewConfigStatus.CURRENT_DRAFT
    )
    svc.set_layout_data(layout.placeholder_name, layout)
    svc.save()
    svc.publish()

    client = Client()

    # no customized color
    response = client.get(reverse("shuup:index"))
    content = response.content.decode("utf-8")
    assert "owl-carousel" in content
    assert ".owl-nav .owl-prev" not in content
    assert ".owl-nav .owl-next" not in content
    assert ".owl-dot:nth-child(" not in content

    # put colors in arrows
    carousel.arrows_color = "#ffaabb"
    carousel.save()
    response = client.get(reverse("shuup:index"))
    content = response.content.decode("utf-8")
    assert ".owl-nav .owl-prev" in content
    assert ".owl-nav .owl-next" in content
    assert "color: #ffaabb !important;" in content

    # put custom color in dots
    test_slide.inactive_dot_color = "#a1b2c3"
    test_slide.active_dot_color = "#d4e4f6"
    test_slide.save()
    response = client.get(reverse("shuup:index"))
    content = response.content.decode("utf-8")
    assert ".owl-dot:nth-child(1)" in content
    assert "border-color: #a1b2c3 !important" in content
    assert "background-color: #d4e4f6 !important;" in content
