# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

#: ReadtheDocs API URL
#:
#: URL for fetching search results via ReadtheDocs API.
SHUUP_GUIDE_API_URL = "https://readthedocs.org/api/v2/search/?project=shoop-guide&version=latest&"

#: ReadtheDocs link URL
#:
#: URL for manually linking search query link. Query parameters are
#: added to end of URL when constructing link.
SHUUP_GUIDE_LINK_URL = "http://shuup-guide.readthedocs.io/en/latest/search.html?check_keywords=yes&area=default&"

#: Whether or not to fetch search results from ReadtheDocs
#:
#: If true, fetch results via the ReadtheDocs API, otherwise only
#: display a link to RTD search page.
SHUUP_GUIDE_FETCH_RESULTS = True

#: Timeout limit for fetching search results
#:
#: Time limit in seconds before a search result request should
#: timeout, so as not to block search results in case of slow response.
SHUUP_GUIDE_TIMEOUT_LIMIT = 2
