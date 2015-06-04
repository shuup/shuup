# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
import uuid
from shoop.simple_cms.models import Page
from shoop.utils.i18n import get_language_name

CONTENT = """
# Bacon ipsum dolor amet doner ham brisket

Pig tenderloin hamburger sausage pork shankle.
Shoulder chicken alcatra boudin.
[Rump short ribs porchetta shankle bacon.](https://baconipsum.com/)
"""


def initialize_page(**kwargs):
    """
    :rtype: shoop.simple_cms.models.Page
    """
    kwargs.setdefault("_current_language", "en")
    kwargs.setdefault("title", "test")
    kwargs.setdefault("url", str(uuid.uuid4()))
    kwargs.setdefault("content", CONTENT)
    if kwargs.pop("eternal", False):
        kwargs.setdefault("available_from", datetime.datetime(1900, 1, 1))
        kwargs.setdefault("available_to", datetime.datetime(2900, 1, 1))
    page = Page(**kwargs)
    page.full_clean()
    return page


def create_page(**kwargs):
    """
    :rtype: shoop.simple_cms.models.Page
    """
    page = initialize_page(**kwargs)
    page.save()
    return page


def create_multilanguage_page(languages=("fi", "en", "ja", "de"), **kwargs):
    """
    :rtype: shoop.simple_cms.models.Page
    """
    page = initialize_page(**kwargs)
    base_url = page.url
    base_title = page.title

    for lang in languages:
        page.set_current_language(lang)
        page.title = "%s, %s" % (base_title, get_language_name(lang))
        page.url = "%s-%s" % (base_url, lang)
        page.content = "Super interesting content in %s" % get_language_name(lang)
        page.save()
        assert page._parler_meta.root_model.objects.filter(
            master_id=page.pk, language_code=lang, url="%s-%s" % (base_url, lang)
        ).exists()
        assert page.has_translation(lang)
    return page
