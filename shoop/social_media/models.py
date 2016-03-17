# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _
from enumfields import Enum, EnumIntegerField

from shoop.core.models._base import ShoopModel


class SocialMediaLinkType(Enum):
    FACEBOOK = 0
    FLICKR = 1
    GOOGLE_PLUS = 2
    INSTAGRAM = 3
    LINKED = 4
    PINTEREST = 5
    TUMBLR = 6
    TWITTER = 7
    VIMEO = 8
    VINE = 9
    YELP = 10
    YOUTUBE = 11

    class Labels:
        FACEBOOK = _("Facebook")
        FLICKR = _("Flickr")
        GOOGLE_PLUS = _("Google-Plus")
        INSTAGRAM = _("Instagram")
        LINKED = _("Linkedin")
        PINTEREST = _("Pinterest")
        TUMBLR = _("Tumblr")
        TWITTER = _("Twitter")
        VIMEO = _("Vimeo")
        VINE = _("Vine")
        YELP = _("Yelp")
        YOUTUBE = _("Youtube")


@python_2_unicode_compatible
class SocialMediaLink(ShoopModel):
    type = EnumIntegerField(
        SocialMediaLinkType, verbose_name=_("type"), default=SocialMediaLinkType.FACEBOOK,
        help_text=_("Type of social media link.")
    )
    url = models.URLField(
        verbose_name=_(u"URL"), max_length=200, help_text=_("Social media link URL.")
    )
    ordering = models.IntegerField(verbose_name=_(u"ordering"), default=0, blank=True, null=True)
    icon_classes = {
        SocialMediaLinkType.FACEBOOK: "facebook-square",
        SocialMediaLinkType.FLICKR: "flickr",
        SocialMediaLinkType.GOOGLE_PLUS: "google-plus-square",
        SocialMediaLinkType.INSTAGRAM: "instagram",
        SocialMediaLinkType.LINKED: "linkedin-square",
        SocialMediaLinkType.PINTEREST: "pinterest",
        SocialMediaLinkType.TUMBLR: "tumblr",
        SocialMediaLinkType.TWITTER: "twitter",
        SocialMediaLinkType.VIMEO: "vimeo",
        SocialMediaLinkType.VINE: "vine",
        SocialMediaLinkType.YELP: "yelp",
        SocialMediaLinkType.YOUTUBE: "youtube",
    }

    def __str__(self):
        return str(self.type)

    class Meta:
        verbose_name = _(u"Social Media Link")
        verbose_name_plural = _(u"Social Media Links")
        ordering = ["ordering"]

    @property
    def icon_class_name(self):
        return self.icon_classes.get(self.type, "")
