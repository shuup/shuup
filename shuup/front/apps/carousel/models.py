# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext as _
from enumfields import Enum, EnumIntegerField
from filer.fields.image import FilerImageField
from parler.managers import TranslatableQuerySet
from parler.models import TranslatedFields

from shuup.core.models import Category, Product
from shuup.core.models._base import ShuupModel, TranslatableShuupModel
from shuup.simple_cms.models import Page


class CarouselMode(Enum):
    SLIDE = 0
    FADE = 1

    class Labels:
        SLIDE = _("Slide")
        FADE = _("Fade")


class LinkTargetType(Enum):
    CURRENT = 0
    NEW = 1

    class Labels:
        CURRENT = _("Current")
        FADE = _("New")


class SlideQuerySet(TranslatableQuerySet):
    def visible(self, dt=None):
        """
        Get slides that should be publicly visible.

        This does not do permission checking.

        :param dt: Datetime for visibility check
        :type dt: datetime.datetime
        :return: QuerySet of slides.
        :rtype: QuerySet[Slide]
        """
        if not dt:
            dt = now()
        q = Q(available_from__lte=dt) & (Q(available_to__gte=dt) | Q(available_to__isnull=True))
        qs = self.filter(q)
        return qs


@python_2_unicode_compatible
class Carousel(ShuupModel):
    name = models.CharField(
        verbose_name=_(u"name"), max_length=50, help_text=_("Name is only used to configure carousels.")
    )
    animation = EnumIntegerField(
        CarouselMode, verbose_name=_("animation"), default=CarouselMode.SLIDE,
        help_text=_("Animation type for cycling slides.")
    )
    interval = models.IntegerField(
        verbose_name=_(u"interval"), default=5, help_text=_("Slide interval in seconds.")
    )
    pause_on_hover = models.BooleanField(
        verbose_name=_(u"pause on hover"),
        default=True, help_text=_("Pauses the cycling of the carousel on mouse over.")
    )
    is_arrows_visible = models.BooleanField(verbose_name=_("show navigation arrows"), default=True)
    use_dot_navigation = models.BooleanField(verbose_name=_("show navigation dots"), default=True)
    image_width = models.IntegerField(
        verbose_name=_(u"image width"), default=1200,
        help_text=_("Slide images will be cropped to this width.")
    )
    image_height = models.IntegerField(
        verbose_name=_("image height"), default=600,
        help_text=_("Slide images will be cropped to this height.")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Carousel")
        verbose_name_plural = _("Carousels")

    @property
    def animation_class_name(self):
        return "fade" if self.animation == CarouselMode.FADE else "slide"


@python_2_unicode_compatible
class Slide(TranslatableShuupModel):
    carousel = models.ForeignKey(Carousel, related_name="slides", on_delete=models.CASCADE)
    name = models.CharField(
        verbose_name=_(u"name"), max_length=50, blank=True, null=True,
        help_text=_("Name is only used to configure slides.")
    )
    product_link = models.ForeignKey(Product, verbose_name=_("product link"), blank=True, null=True)
    category_link = models.ForeignKey(Category, verbose_name=_("category link"), blank=True, null=True)
    cms_page_link = models.ForeignKey(Page, verbose_name=_("cms page link"), blank=True, null=True)
    ordering = models.IntegerField(verbose_name=_("ordering"), default=0, blank=True, null=True)
    target = EnumIntegerField(
        LinkTargetType, verbose_name=_("link target"), default=LinkTargetType.CURRENT,
    )
    available_from = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('available from'),
    )
    available_to = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('available to'),
    )

    translations = TranslatedFields(
        caption=models.CharField(verbose_name=_("caption"), max_length=80, blank=True, null=True),
        caption_text=models.TextField(
            verbose_name=_("caption text"),
            blank=True,
            null=True,
            help_text=_("When displayed in banner box mode, caption text is shown as a tooltip"),
        ),
        external_link=models.CharField(verbose_name=_("external link"), blank=True, null=True, max_length=160),
        image=FilerImageField(verbose_name=_("image"), blank=True, null=True, on_delete=models.PROTECT)
    )

    def __str__(self):
        return "%s %s" % (_("Slide"), self.pk)

    class Meta:
        verbose_name = _("Slide")
        verbose_name_plural = _("Slides")
        ordering = ("ordering", "id")

    def get_translated_field(self, attr):
        if not self.safe_translation_getter(attr):
            return self.safe_translation_getter(attr, language_code=settings.PARLER_DEFAULT_LANGUAGE_CODE)
        return getattr(self, attr)

    def get_link_url(self):
        """
        Get right link url for this slide.

        Initially external link is used. If not set link will fallback to
        product_link, external_link or cms_page_link in this order.

        :return: return correct link url for slide if set
        :rtype: str|None
        """
        external_link = self.get_translated_field("external_link")
        if external_link:
            return external_link
        elif self.product_link:
            return reverse("shuup:product", kwargs=dict(pk=self.product_link.pk, slug=self.product_link.slug))
        elif self.category_link:
            return reverse("shuup:category", kwargs=dict(pk=self.category_link.pk, slug=self.category_link.slug))
        elif self.cms_page_link:
            return reverse("shuup:cms_page", kwargs=dict(url=self.cms_page_link.url))

    def is_visible(self, dt=None):
        """
        Get slides that should be publicly visible.

        This does not do permission checking.

        :param dt: Datetime for visibility check
        :type dt: datetime.datetime
        :return: Public visibility status
        :rtype: bool
        """
        if not dt:
            dt = now()

        return (
            (self.available_from and self.available_from <= dt) and
            (self.available_to is None or self.available_to >= dt)
        )

    def get_link_target(self):
        """
        Return link target type string based on selection

        :return: Target type string
        :rtype: str
        """
        if self.target == LinkTargetType.NEW:
            return "_blank"
        else:
            return "_self"

    objects = SlideQuerySet.as_manager()
