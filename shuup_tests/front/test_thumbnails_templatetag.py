# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import base64
import pytest
from easy_thumbnails.files import Thumbnailer
from io import BytesIO

from shuup.core import cache
from shuup.core.models import ProductMedia
from shuup.front.templatetags.thumbnails import _get_cached_thumbnail_url, thumbnail
from shuup.testing import factories


def setup_function(fn):
    cache.clear()


def test_thumbnailing_none():
    assert thumbnail(None) is None


@pytest.mark.django_db
def test_thumbnail_cache():
    image1 = factories.get_random_filer_image()
    image2 = factories.get_random_filer_image()
    media = ProductMedia.objects.create(product=factories.get_default_product(), file=image2)

    cache_key, cached_url = _get_cached_thumbnail_url(image1, alias=None, generate=True)
    assert cache_key and not cached_url
    url = thumbnail(image1)
    cache_key, cached_url = _get_cached_thumbnail_url(image1, alias=None, generate=True)
    assert cache_key and cached_url == url

    cache_key, cached_url = _get_cached_thumbnail_url(media, alias=None, generate=True)
    assert cache_key and not cached_url
    url = thumbnail(media)
    cache_key, cached_url = _get_cached_thumbnail_url(media, alias=None, generate=True)
    assert cache_key and cached_url == url

    img_url = "http://www.shuup.com/logo.png"
    cache_key, cached_url = _get_cached_thumbnail_url(img_url, alias=None, generate=True)
    assert cache_key and not cached_url
    url = thumbnail(img_url)
    cache_key, cached_url = _get_cached_thumbnail_url(img_url, alias=None, generate=True)
    assert cache_key and cached_url == url

    source = Thumbnailer(file=BytesIO(TEST_PNG), name="logo.png")
    source.url = "/media/logo.png"
    cache_key, cached_url = _get_cached_thumbnail_url(source, alias=None, generate=True)
    assert cache_key and not cached_url
    url = thumbnail(source)
    cache_key, cached_url = _get_cached_thumbnail_url(source, alias=None, generate=True)
    assert cache_key and cached_url == url

    # check whether caches are bumped
    image1.save()
    cache_key, cached_url = _get_cached_thumbnail_url(image1, alias=None, generate=True)
    assert cache_key and not cached_url

    media.save()
    cache_key, cached_url = _get_cached_thumbnail_url(media, alias=None, generate=True)
    assert cache_key and not cached_url

    media.delete()
    image1.delete()
    image2.delete()


def test_thumbnailing_with_none_as_thumbnailer():
    source = Thumbnailer(file=BytesIO(TEST_PNG), name="test.png")
    source.easy_thumbnails_thumbnailer = None
    assert thumbnail(source) is None


def test_thumbnailing_svg_without_xml_header():
    assert do_thumbnailing(TEST_SVG, "test.svg") == "/media/test.svg"


def test_thumbnailing_svg_with_xml_header():
    assert do_thumbnailing(TEST_SVG2, "test2.svg") == "/media/test2.svg"


def test_thumbnailing_svg_without_url():
    source = Thumbnailer(file=BytesIO(TEST_SVG), name="test.svg")
    assert not hasattr(source, "url")
    assert thumbnail(source) is None


@pytest.mark.django_db
def test_thumbnailing_png():
    url = do_thumbnailing(TEST_PNG, "test.png")
    assert url.startswith("/media/")
    assert "test.png.128x128" in url


@pytest.mark.django_db
def test_thumbnailing_with_str_size():
    url = do_thumbnailing(TEST_PNG, "test.png", size="42x42")
    assert "test.png.42x42" in url


def test_thumbnailing_with_invalid_size():
    with pytest.raises(ValueError) as exc_info:
        do_thumbnailing(TEST_PNG, "test.png", size="foobar")
    assert "{}".format(exc_info.value) == "Error! %r is not a valid size." % "foobar"


def test_thumbnailing_carbage():
    assert do_thumbnailing(b"junk", "junk") is None


def test_thumbnailing_nonseekable_svg_file():
    class DummyFile(BytesIO):
        def tell(self):
            raise IOError("Error! DummyFile does not support tell/seek.")

        seek = tell

    source = Thumbnailer(file=DummyFile(TEST_SVG), name="test.svg")
    source.url = "/media/test.svg"

    # Well if the merchant tries his luck with non seekable file
    # and decides to name it as svg then he might not have working
    # front. Also not worth thumbnail these anyways so might as well
    # return the source url.
    assert thumbnail(source) == source.url


def do_thumbnailing(content, name, *args, **kwargs):
    source = Thumbnailer(file=BytesIO(content), name=name)
    source.url = "/media/" + name
    return thumbnail(source, *args, **kwargs)


TEST_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" height="1985" width="1985">'
    b'<defs><clipPath id="a">'
    b'<circle r="992" cy="992" cx="992"/>'
    b"</clipPath>"
    b"</defs>"
    b'<circle r="992" cy="992" cx="992" fill="#1bab95"/>'
    b'<path clip-path="url(#a)" d="'
    b"M1436.502 355.512L533.336 498.785v542.68L861.62 1369.72 465.5 "
    b"1593.51l397.107 393.007 1116.107-11.013c0-30.237 10.208-1054.745 "
    b'7.557-1084.294z" fill="#17907d"/>'
    b'<path d="M936.31 511.387c.09 32.09.183 64.18.274 '
    b"96.268h500.766V356.398c-225.075.807-450.214-1.666-675.246 "
    b"1.333-106.022 3.94-225.723 43.89-273.074 147.278-50.426 106.126-42.21 "
    b"227.55-36.2 341.678 8.19 98.885 55.278 204.434 151.92 244.722 116.764 "
    b"51.967 246.81 32.976 370.813 "
    b"36.71h144.092c-.49-35.122-.982-70.244-1.473-105.365l269.44 "
    b"222.04-269.44 "
    b"235.497v-100.93c-217.853-6.475-435.65-15.13-653.282-26.91v242.283c255.997 "
    b"19.84 512.692 36.406 769.555 35.167 104.486-2.236 222.213-41.453 "
    b"269.732-142.53 50.638-102.356 38.175-219.444 "
    b"37.728-329.98-3.492-103.973-47.213-219.18-149.015-262"
    b".92-111.582-50.82-236.435-31.735-355.204-35.56H936.01l.3 "
    b"103.282-262.707-222.04C761.17 663.9 848.745 587.625 "
    b'936.31 511.387z" fill="#fff"/></svg>'
)


TEST_SVG2 = b'<?xml version="1.0" encoding="UTF-8"?>\n' + TEST_SVG

TEST_PNG = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAIAAAACABAMAAAAxEHz4AAAAElBMVEV/goLJ1c3O1NPx8f"
    b"Grra8rn42fE51OAAAABnRSTlMByXT//+1WpT4PAAACeUlEQVRo3u1Za3LbIBCW5QuEivxX"
    b"lRwgHtYHIKv87zTV/a9SQBJCSYAVa1dtRysLbMasv32wD7mqDjrooDWdTt3XdArGrmujDJ"
    b"6UUqC+JljGlyQDQzh+FyOsUgxg3A7+99yFalwfR0wzgBHAR0HmNTdnRcgRvMqIHp9QESnC"
    b"4By1wUd6YIkQR8Bm0CAbATIZwN46oIsQMeMZdlei9/Y+RkizQrBDmiskmiv3hQia3c8C/z"
    b"jvf5i4CJ7zjtTQ/EAbB9LOg9wopZmtU0ndZPwAmK7MD+uKG9aZZmz+h5A2xwM5BZMgsGiK"
    b"GRdPlDLcK5wjubW0CNyIxE8syAwo55vlhd0YPH8WAbadhfnrF+cFYrGeFuuIlPVEYXcIu0"
    b"vaUbvBOlSzPbmiH3rwjnS/vAB/KqSx/SAbE8E1BtMF6tMZyVcoWptkIqSbjU1FJ3GLCNpY"
    b"X0spplmKb52YYwkpqAIgor/NAN8NjkdkBFXrl8MvRlgXhoYBy81otDEMC4Tt1fpFPBoGHs"
    b"L2lkdbAMPwXqyDiwPgIWzXwWXcP2thOwOYGEwQCuqDtxWEghJnDaEkoMwQ3ks71xWEtqTA"
    b"CCGU1UgBhLLmOzBEWb8QaKGwUr16LRQWmguE0lrZayHXL2Qh/ChNLG9pBk0+N84QirNzGg"
    b"IhuUISAqVaT0Kg9AtJQ5D6hWuCAalfSGmBVmAktECsUOIMzkAq064JEUgMIGEFRdcCp0qD"
    b"mCORC83r8JNXJ0LkMNEfBw7//vPEotx40wcQd3sw/RdYganEqqt5CAxxGdTIE+EmCKD3/8"
    b"r0avq0NPI4vovroKpb+6oqM9VVa+7arNlrWW+P/wQPugf9BrjgquyoOpPWAAAAAElFTkSu"
    b"QmCC"
)
