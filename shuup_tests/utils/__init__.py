# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import contextlib
import django.conf
import logging
import string
import sys
import types
import uuid
from bs4 import BeautifulSoup
from django.test import Client, TestCase, override_settings
from django.utils.crypto import get_random_string
from django.utils.timezone import now

from shuup.utils.django_compat import clear_url_caches, get_urlconf, set_urlconf


def printable_gibberish(length=10):
    return get_random_string(length, allowed_chars=string.ascii_lowercase)


class SmartClient(Client):
    def soup(self, path, data=None, method="get"):
        response = getattr(self, method)(path=path, data=data)
        assert 200 <= response.status_code <= 299, "Valid status"
        return BeautifulSoup(response.content, "lxml")

    def response_and_soup(self, path, data=None, method="get"):
        response = getattr(self, method)(path=path, data=data)
        return (response, BeautifulSoup(response.content, "lxml"))


def empty_iterable(obj):
    for x in obj:
        return False
    return True


def prepare_logger_for_stdout(logger, level=logging.DEBUG):
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(fmt=logging.BASIC_FORMAT)
    handler.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(handler)
    if level is not None:
        logger.setLevel(level)


@contextlib.contextmanager
def replace_urls(patterns, extra=None):
    """
    Context manager to replace the root URLconf with a list of URLpatterns in-memory.

    This is admittedly somewhat black-magicky.

    :param patterns: List of URLpatterns
    :type patterns: list[RegexURLResolver]
    :param extra: Dict to add to the created urlconf
    :type extra: dict
    """
    old_urlconf = get_urlconf(default=django.conf.settings.ROOT_URLCONF)
    urlconf_module_name = "replace_urls_%s" % uuid.uuid4()
    module = types.ModuleType(urlconf_module_name)
    module.urlpatterns = patterns
    module.__dict__.update(extra or ())
    sys.modules[urlconf_module_name] = module
    set_urlconf(urlconf_module_name)
    clear_url_caches()
    with override_settings(ROOT_URLCONF=urlconf_module_name):
        yield
    set_urlconf(old_urlconf)
    clear_url_caches()
    sys.modules.pop(urlconf_module_name)


def error_code_test(errors, expect_flag, code):
    errors = list(errors)
    for error in errors:
        if error.code == code:
            if expect_flag:
                return True
            else:
                raise ValueError("Error! Code %r found in %r, did not expect it." % (code, errors))
    if expect_flag:
        raise ValueError("Error! Code %r not found in %r, did expect it." % (code, errors))
    return True


def error_exists(errors, code):
    return error_code_test(errors, True, code)


def error_does_not_exist(errors, code):
    return error_code_test(errors, False, code)


def very_recently(datetime, how_recently=1):
    return abs(datetime - now()).total_seconds() < how_recently


def atomic_commit_mock(func):
    # make it atomic, don't commit after the transaction commit
    func()


_test_case = TestCase("setUp")  # gotta pass something to the ctor.

assert_contains = _test_case.assertContains
assert_not_contains = _test_case.assertNotContains
