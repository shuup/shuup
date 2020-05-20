# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import reversion
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumField
from filer.fields.image import FilerImageField
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields

from shuup.core.fields import InternalIdentifierField
from shuup.utils.analog import define_log_model, LogEntryKind


class PageOpenGraphType(Enum):
    Website = "website"
    Article = "article"

    class Labels:
        Website = _("Website")
        Article = _("Article")


class PageQuerySet(TranslatableQuerySet):

    def not_deleted(self):
        return self.filter(deleted=False)

    def visible(self, shop, dt=None, user=None):
        """
        Get pages that should be publicly visible.

        This does not do permission checking.

        :param dt: Datetime for visibility check.
        :type dt: datetime.datetime
        :return: QuerySet of pages.
        :rtype: QuerySet[Page]
        """
        if not dt:
            dt = now()
        q = Q(
            Q(available_from__lte=dt)
            & (Q(available_to__gte=dt) | Q(available_to__isnull=True))
        )
        if user and not user.is_anonymous():
            q |= Q(created_by=user)
        qs = self.not_deleted().for_shop(shop).filter(q)
        return qs

    def for_shop(self, shop):
        return self.filter(shop=shop)


@reversion.register(follow=["translations"])
@python_2_unicode_compatible
class Page(MPTTModel, TranslatableModel):
    shop = models.ForeignKey("shuup.Shop", verbose_name=_('shop'))
    supplier = models.ForeignKey("shuup.Supplier", null=True, blank=True, verbose_name=_('supplier'))
    available_from = models.DateTimeField(
        default=now, null=True, blank=True, db_index=True,
        verbose_name=_('available since'), help_text=_(
            "Set an available date to restrict the page to be available only after a certain date and time. "
            "This is useful for pages describing sales campaigns or other time-sensitive pages."
        )
    )
    available_to = models.DateTimeField(
        null=True, blank=True, db_index=True,
        verbose_name=_('available until'), help_text=_(
            "Set an available date to restrict the page to be available only until a certain date and time. "
            "This is useful for pages describing sales campaigns or other time-sensitive pages."
        )
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="+", on_delete=models.SET_NULL,
        verbose_name=_('created by')
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="+", on_delete=models.SET_NULL,
        verbose_name=_('modified by')
    )

    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('created on'))
    modified_on = models.DateTimeField(auto_now=True, editable=False, verbose_name=_('modified on'))

    identifier = InternalIdentifierField(
        unique=False,
        help_text=_('This identifier can be used in templates to create URLs'),
        editable=True
    )

    visible_in_menu = models.BooleanField(verbose_name=_("visible in menu"), default=False, help_text=_(
        "Enable this if this page should have a visible link in the top menu of the store front."
    ))
    parent = TreeForeignKey(
        "self", blank=True, null=True, related_name="children", verbose_name=_("parent"), help_text=_(
            "Set this to a parent page if this page should be subcategorized (sub-menu) under another page."
        ))
    list_children_on_page = models.BooleanField(verbose_name=_("display children on page"), default=False, help_text=_(
        "Enable this if this page should display all of its children pages."
    ))
    show_child_timestamps = models.BooleanField(verbose_name=_("show child page timestamps"), default=True, help_text=_(
        "Enable this if you want to show timestamps on the child pages. Please note, that this "
        "requires the children to be listed on the page as well."
    ))
    deleted = models.BooleanField(default=False, verbose_name=_("deleted"))

    translations = TranslatedFields(
        title=models.CharField(max_length=256, verbose_name=_('title'), help_text=_(
            "The page title. This is shown anywhere links to your page are shown."
        )),
        url=models.CharField(
            max_length=100, verbose_name=_('URL'),
            default=None,
            blank=True,
            null=True,
            help_text=_(
                "The page url. Choose a descriptive url so that search engines can rank your page higher. "
                "Often the best url is simply the page title with spaces replaced with dashes."
            )
        ),
        content=models.TextField(verbose_name=_('content'), help_text=_(
            "The page content. This is the text that is displayed when customers click on your page link."
            "You can leave this empty and add all page content through placeholder editor in shop front."
            "To edit the style of the page you can use the Snippet plugin which is in shop front editor."
        ))
    )
    template_name = models.TextField(
        max_length=500,
        verbose_name=_("Template path"),
        default=settings.SHUUP_SIMPLE_CMS_DEFAULT_TEMPLATE
    )
    render_title = models.BooleanField(verbose_name=_("render title"), default=True, help_text=_(
        "Enable this if this page should have a visible title."
    ))

    objects = TreeManager.from_queryset(PageQuerySet)()

    class Meta:
        ordering = ('-id',)
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        unique_together = ("shop", "identifier")

    def delete(self, using=None):
        raise NotImplementedError("Error! Not implemented: `Page` -> `delete()`. Use `soft_delete()` instead.")

    def soft_delete(self, user=None):
        if not self.deleted:
            self.deleted = True
            self.add_log_entry("Success! Deleted (soft).", kind=LogEntryKind.DELETION, user=user)
            # Bypassing local `save()` on purpose.
            super(Page, self).save(update_fields=("deleted",))

    def clean(self):
        url = getattr(self, "url", None)
        if url:
            page_translation = self._meta.model._parler_meta.root_model
            shop_pages = Page.objects.for_shop(self.shop).exclude(deleted=True).values_list("id", flat=True)
            url_checker = page_translation.objects.filter(url=url, master_id__in=shop_pages)
            if self.pk:
                url_checker = url_checker.exclude(master_id=self.pk)
            if url_checker.exists():
                raise ValidationError(_("URL already exists."), code="invalid_url")

    def is_visible(self, dt=None):
        if not dt:
            dt = now()

        return (
            (self.available_from and self.available_from <= dt)
            and (self.available_to is None or self.available_to >= dt)
        )

    def save(self, *args, **kwargs):
        with reversion.create_revision():
            super(Page, self).save(*args, **kwargs)

    def get_html(self):
        return self.content

    @classmethod
    def create_initial_revision(cls, page):
        from reversion.models import Version
        if not Version.objects.get_for_object(page).exists():
            with reversion.create_revision():
                page.save()

    def __str__(self):
        return force_text(self.safe_translation_getter("title", any_language=True, default=_("Untitled")))


@python_2_unicode_compatible
class PageOpenGraph(TranslatableModel):
    """
    Object that describes Open Graph extra meta attributes.
    """
    page = models.OneToOneField(Page, verbose_name=_('page'), related_name="open_graph")

    image = FilerImageField(
        verbose_name=_("Image"),
        blank=True, null=True,
        on_delete=models.SET_NULL,
        help_text=_("The image of your object."), related_name="blog_meta_image"
    )
    og_type = EnumField(PageOpenGraphType, verbose_name=_("type"), default=PageOpenGraphType.Website)
    translations = TranslatedFields(
        title=models.CharField(max_length=100, blank=True, verbose_name=_("Title"), help_text=_(
            'The title of your object as it should appear within the graph, e.g. The Rock.'
        )),
        description=models.TextField(max_length=160, blank=True, verbose_name=_("Description"), help_text=_(
            "A one to two sentence description of your object."
        )),
        section=models.CharField(max_length=256, blank=True, verbose_name=_("Section"), help_text=_(
            "A high-level section name, e.g. Technology. Only applicable when type is Article."
        )),
        tags=models.CharField(max_length=256, blank=True, verbose_name=_("Tags"), help_text=_(
            "Tag words associated with this article. Only applicable when type is Article."
        )),
        article_author=models.CharField(max_length=100, blank=True, verbose_name=_("Article author"), help_text=_(
            'The name of the author for the article. Only applicable when type is Article.'
        ))
    )

    def __str__(self):
        return force_text(self.page)


PageLogEntry = define_log_model(Page)
