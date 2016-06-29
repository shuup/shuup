# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError

from shuup.simple_cms.admin_module.views import PageEditView, PageForm
from shuup_tests.simple_cms.utils import create_multilanguage_page, create_page
from shuup_tests.utils.forms import get_form_data


@pytest.mark.django_db
def test_url_uniqueness(rf):
    page = create_page(url='bacon')
    with pytest.raises(ValidationError):
        page = create_page(url='bacon')

    with transaction.atomic():
        mpage = create_multilanguage_page(url="cheese")
        with pytest.raises(IntegrityError):
            mpage = create_multilanguage_page(url="cheese")


@pytest.mark.django_db
def test_page_form(rf):
    view = PageEditView(request=rf.get("/"))
    form_class = view.get_form_class()
    form_kwargs = view.get_form_kwargs()
    form = form_class(**form_kwargs)
    assert not form.is_bound

    data = get_form_data(form)
    data.update({
        "available_from": "",
        "available_to": "",
        "content__en": "",
        "content__fi": "suomi",
        "content__ja": "",
        "identifier": "",
        "title__en": "",
        "title__fi": "",
        "title__ja": "",
        "url__en": "",
        "url__fi": "suomi",
        "url__ja": "",
    })

    form = form_class(**dict(form_kwargs, data=data))
    form.full_clean()
    assert "title__fi" in form.errors  # We get an error because all of a given language's fields must be filled if any are
    data["title__fi"] = "suomi"
    form = form_class(**dict(form_kwargs, data=data))
    form.full_clean()
    assert not form.errors
    page = form.save()
    assert set(page.get_available_languages()) == {"fi"}  # The page should be only in Finnish
    # Let's edit that page
    original_url = "errrnglish"
    data.update({"title__en": "englaish", "url__en": original_url, "content__en": "ennnn ennnn ennnnnnn-nn-n-n"})
    form = form_class(**dict(form_kwargs, data=data, instance=page))
    form.full_clean()
    assert not form.errors
    page = form.save()
    assert set(page.get_available_languages()) == {"fi", "en"}  # English GET

    # add dummy page with simple url, page is in english
    dummy = create_page(url="test")

    # edit page again and try to set duplicate url
    data.update({"title__en": "englaish", "url__en": "test", "content__en": "ennnn ennnn ennnnnnn-nn-n-n"})
    form = form_class(**dict(form_kwargs, data=data, instance=page))
    form.full_clean()

    assert len(form.errors) == 1
    assert "url__en" in form.errors
    assert form.errors["url__en"].as_data()[0].code == "invalid_url"

    # it should be possible to change back to the original url
    data.update({"title__en": "englaish", "url__en": original_url, "content__en": "ennnn ennnn ennnnnnn-nn-n-n"})
    form = form_class(**dict(form_kwargs, data=data, instance=page))
    form.full_clean()
    assert not form.errors
    page = form.save()

    # add finnish urls, it should not be possible to enter original url
    data.update({"title__fi": "englaish", "url__fi": original_url, "content__fi": "ennnn ennnn ennnnnnn-nn-n-n"})
    form = form_class(**dict(form_kwargs, data=data, instance=page))
    form.full_clean()
    assert len(form.errors) == 1
    assert "url__fi" in form.errors
    assert form.errors["url__fi"].as_data()[0].code == "invalid_url"
