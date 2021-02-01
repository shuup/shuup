# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import time

import requests


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


def retry_request(n_retries=5, **kwargs):
    """
    Retry a `requests` request with exponential backoff up to `n_retries` times.

    :param n_retries: Maximum retries
    :type n_retries: int
    :param kwargs: Kwargs to pass to `requests.request()`.
    :return: Requests response.
    :rtype: requests.Response
    """
    exc = resp = None
    for n_try in range(n_retries):
        try:
            exc = None
            resp = requests.request(**kwargs)
            if resp.status_code < 500:
                return resp
        except requests.RequestException:
            pass

        time.sleep((2 ** (n_try + 1)) * 0.5)

    if exc:
        raise exc

    if resp:
        resp.raise_for_status()

    raise Exception("Error! An unknown problem occurred with the request.")
