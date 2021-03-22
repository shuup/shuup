# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from jinja2 import Environment
from jinja2.runtime import Context

from shuup.front.middleware import ShuupFrontMiddleware
from shuup.testing.factories import get_default_shop


def get_request(path="/", user=None):
    request = RequestFactory().get(path)
    request.user = user or AnonymousUser()
    return request


def get_request_with_basket(path="/", user=None, ajax=False):
    request = get_request(path, user)
    get_default_shop()  # Create a Shop
    SessionMiddleware().process_request(request)
    MessageMiddleware().process_request(request)
    ShuupFrontMiddleware().process_request(request)
    request.session = {}
    if ajax:
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"
    return request


def get_jinja_context(path="/", user=None, **vars):
    env = Environment()
    ctx = Context(environment=env, parent=None, name="FauxContext", blocks={})
    if "request" not in vars:
        vars["request"] = get_request_with_basket(path, user=user)
    ctx.vars.update(vars)
    return ctx
