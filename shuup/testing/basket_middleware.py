# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.basket.command_middleware import BaseBasketCommandMiddleware


class TestBasketCommandMiddleware(BaseBasketCommandMiddleware):
    def preprocess_kwargs(self, basket, request, command: str, kwargs: dict) -> dict:
        kwargs["extra"] = kwargs.get("extra") or {}
        kwargs["extra"]["extra"] = kwargs["extra"].get("extra") or {}
        kwargs["extra"]["extra"]["line_options"] = "works"
        return kwargs

    def postprocess_response(self, basket, request, command: str, kwargs: dict, response: dict) -> dict:
        response["it_works"] = True
        return response
