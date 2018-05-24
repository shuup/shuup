# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


def get_cookie_consent_data(cookie_categories, documents):
    """
    :param list[GDPRCookieCategory] cookie_categories:
    :param list[simple_cms.Page] documents:
    """
    consent_cookies = [cookie_category.cookies for cookie_category in cookie_categories]
    consent_cookies = list(set(",".join(consent_cookies).replace(" ", "").split(",")))

    return {
        "cookies": consent_cookies,
        "cookie_categories": [cookie_category.id for cookie_category in cookie_categories],
        "documents": [
            dict(url=consent_document.url, id=consent_document.id)
            for consent_document in documents
        ]
    }
