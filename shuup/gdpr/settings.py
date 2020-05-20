# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

# The cookie name that will save the consent in the user browser.
SHUUP_GDPR_CONSENT_COOKIE_NAME = "shuup_gdpr_consent"


SHUUP_GDPR_DEFAULT_BANNER_STRING = _("<p>This website stores cookies on your computer. "
                                     "These cookies are used to collect information about how you interact with our "
                                     "website and allow us to remember you. We use this information in order to "
                                     "improve and customize your browsing experience and for analytics and metrics "
                                     "about our visitors both on this website and other media. To find out more "
                                     "about the cookies we use, see our Privacy Policy.</p>")


SHUUP_GDPR_DEFAULT_EXCERPT_STRING = _("<p>When you visit any website, it may store or retrieve information on your"
                                      "browser, mostly in the form of cookies. This information might be about you, "
                                      "your preferences or your device and is mostly used to make the site work as "
                                      "you expect it to. The information does not usually directly identify you, "
                                      "but it can give you a more personalized web experience.</p>"
                                      "<p>Because we respect your right to privacy, you can choose not to allow some "
                                      "types of cookies. Click on the different category headings to find out more "
                                      "and change our default settings. However, blocking some types of cookies may "
                                      "impact your experience of the site and the services we are able to offer.</p>")

GDPR_PRIVACY_POLICY_PAGE_URLS = {
    "en": "privacy-policy",
    "fi": "tietosuojakäytäntö",
    "it": "politica-di-riservatezza",
    "ja": "個人情報保護方針",
    "pt-br": "política-de-privacidade",
    "sv": "integritetspolicy",
    "zh-hans": "隐私政策"
}
