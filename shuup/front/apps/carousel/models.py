# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from easy_thumbnails.files import get_thumbnailer
from enumfields import Enum, EnumIntegerField
from filer.fields.image import FilerImageField
from parler.managers import TranslatableQuerySet
from parler.models import TranslatedFields

from shuup.core.fields import HexColorField
from shuup.core.models import Category, Product
from shuup.core.models._base import ShuupModel, TranslatableShuupModel
from shuup.simple_cms.models import Page
from shuup.utils.django_compat import reverse


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
        CURRENT = _("Current page")
        NEW = _("New page")


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
    shops = models.ManyToManyField(
        "shuup.Shop",
        related_name="carousels",
        verbose_name=_("shops"),
        help_text=_("Select which shops you would like the carousel to be visible in."),
    )
    name = models.CharField(
        max_length=50, verbose_name=_("name"), help_text=_("The carousel name use for carousel configuration.")
    )
    animation = EnumIntegerField(
        CarouselMode,
        default=CarouselMode.SLIDE,
        verbose_name=_("animation"),
        help_text=_("Animation type for cycling slides."),
    )
    interval = models.IntegerField(default=5, verbose_name=_("interval"), help_text=_("Slide interval in seconds."))
    pause_on_hover = models.BooleanField(
        default=True,
        verbose_name=_("pause on hover"),
        help_text=_("When checked, the carousel cycling pauses on mouse over."),
    )
    is_arrows_visible = models.BooleanField(
        default=True,
        verbose_name=_("show navigation arrows"),
        help_text=_(
            "When checked, navigational arrows are shown on the carousel allowing for customers to go back and forward."
        ),
    )
    use_dot_navigation = models.BooleanField(
        default=True,
        verbose_name=_("show navigation dots"),
        help_text=_("When checked, navigational indicator dots are shown."),
    )
    image_width = models.IntegerField(
        default=1200, verbose_name=_("image width"), help_text=_("Slide images will be cropped to this width.")
    )
    image_height = models.IntegerField(
        default=600, verbose_name=_("image height"), help_text=_("Slide images will be cropped to this height.")
    )
    arrows_color = HexColorField(
        verbose_name=_("Arrows color"),
        blank=True,
        null=True,
        help_text=_("Set the custom color for the arrows."),
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
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("name"),
        help_text=_("Name is only used to configure slides."),
    )
    product_link = models.ForeignKey(
        Product,
        related_name="+",
        blank=True,
        null=True,
        verbose_name=_("product link"),
        help_text=_("Set the product detail page that should be shown when this slide is clicked, if any."),
        on_delete=models.CASCADE,
    )
    category_link = models.ForeignKey(
        Category,
        related_name="+",
        blank=True,
        null=True,
        verbose_name=_("category link"),
        help_text=_("Set the product category page that should be shown when this slide is clicked, if any."),
        on_delete=models.CASCADE,
    )
    cms_page_link = models.ForeignKey(
        Page,
        related_name="+",
        verbose_name=_("cms page link"),
        blank=True,
        null=True,
        help_text=_("Set the web page that should be shown when the slide is clicked, if any."),
        on_delete=models.CASCADE,
    )
    ordering = models.IntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name=_("ordering"),
        help_text=_(
            "Set the numeric order in which this slide should appear relative to other slides in this carousel."
        ),
    )
    target = EnumIntegerField(
        LinkTargetType,
        default=LinkTargetType.CURRENT,
        verbose_name=_("link target"),
        help_text=_("Set this to current if clicking on this slide should open a new browser tab."),
    )
    available_from = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("available since"),
        help_text=_(
            "Set the date and time, starting from which this slide should be visible in the carousel. "
            "This is useful to advertise sales campaigns or other time-sensitive marketing."
        ),
    )
    available_to = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("available until"),
        help_text=_(
            "Set the date and time, until which this slide should be visible in the carousel. "
            "This is useful to advertise sales campaigns or other time-sensitive marketing."
        ),
    )
    inactive_dot_color = HexColorField(
        verbose_name=_("Inactive dot border color"),
        blank=True,
        null=True,
        help_text=_("Customize the dot border color when slide is not active."),
    )
    active_dot_color = HexColorField(
        verbose_name=_("Active dot color"),
        blank=True,
        null=True,
        help_text=_("Customize the dot color when slide is active."),
    )

    translations = TranslatedFields(
        caption=models.CharField(
            max_length=80,
            blank=True,
            null=True,
            verbose_name=_("caption"),
            help_text=_(
                "Text that describes the image. It is displayed on top of the image if 'Render "
                "image text' box is enabled in front-end. Also used for search engine purposes."
            ),
        ),
        caption_text=models.TextField(
            blank=True,
            null=True,
            verbose_name=_("caption text"),
            help_text=_(
                "Caption text is displayed as secondary text on top of the image if "
                "'Render image text' box is enabled in front-end for 'Carousel plugin' type "
                "(disabled for 'Banner box' type). It is also shown as a tooltip."
            ),
        ),
        external_link=models.CharField(
            max_length=800,
            blank=True,
            null=True,
            verbose_name=_("external link"),
            help_text=_("Set the external site that should be shown when this slide is clicked, if any."),
        ),
        image=FilerImageField(
            blank=True,
            null=True,
            related_name="+",
            verbose_name=_("image"),
            on_delete=models.PROTECT,
            help_text=_("The slide image to show."),
        ),
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

        return (self.available_from and self.available_from <= dt) and (
            self.available_to is None or self.available_to >= dt
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

    @property
    def easy_thumbnails_thumbnailer(self):
        """
        Get Thumbnailer instance for the translated image.
        Will return None if file cannot be thumbnailed.
        :rtype:easy_thumbnails.files.Thumbnailer|None
        """
        image = self.get_translated_field("image")

        if not image:
            return

        try:
            return get_thumbnailer(image)
        except ValueError:
            return get_thumbnailer(image.filer_image_file)
        except Exception:
            return None

    def get_thumbnail(self, **kwargs):
        """
        Get thumbnail for the translated image
        This will return None if there is no file
        :rtype: easy_thumbnails.files.ThumbnailFile|None
        """
        kwargs.setdefault("size", (self.carousel.image_width, self.carousel.image_height))
        kwargs.setdefault("crop", True)  # sane defaults
        kwargs.setdefault("upscale", True)  # sane defaults

        if kwargs["size"] == (0, 0):
            return None

        thumbnailer = self.easy_thumbnails_thumbnailer

        if not thumbnailer:
            return None

        return thumbnailer.get_thumbnail(thumbnail_options=kwargs)

    objects = SlideQuerySet.as_manager()
