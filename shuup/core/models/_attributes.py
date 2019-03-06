# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import calendar
import datetime
from collections import defaultdict
from decimal import Decimal

import six
from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.template.defaultfilters import yesno
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timesince import timesince
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language
from enumfields import Enum, EnumIntegerField
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields

from shuup.core.fields import InternalIdentifierField
from shuup.core.templatetags.shuup_common import datetime as format_datetime
from shuup.core.templatetags.shuup_common import number as format_number
from shuup.utils.analog import define_log_model
from shuup.utils.dates import parse_date
from shuup.utils.numbers import parse_decimal_string
from shuup.utils.text import flatten

NoSuchAttributeHere = object()


class AttributeVisibility(Enum):
    HIDDEN = 0
    SHOW_ON_PRODUCT_PAGE = 1
    SEARCHABLE_FIELD = 2
    NOT_VISIBLE = 3

    class Labels:
        HIDDEN = _('hidden')
        SHOW_ON_PRODUCT_PAGE = _('shown on product page')
        SEARCHABLE_FIELD = _('searchable metadata')
        NOT_VISIBLE = _('private metadata')


class AttributeType(Enum):
    INTEGER = 1
    BOOLEAN = 2
    DECIMAL = 3
    TIMEDELTA = 4

    DATETIME = 10
    DATE = 11

    TRANSLATED_STRING = 20
    UNTRANSLATED_STRING = 21

    class Labels:
        INTEGER = _('integer')
        DECIMAL = _('decimal')
        BOOLEAN = _('boolean')
        TIMEDELTA = _('time interval')

        DATETIME = _('date and time')
        DATE = _('date only')

        TRANSLATED_STRING = _('translated string')
        UNTRANSLATED_STRING = _('untranslated string')


ATTRIBUTE_STRING_TYPES = (
    AttributeType.TRANSLATED_STRING,
    AttributeType.UNTRANSLATED_STRING,
)

ATTRIBUTE_NUMERIC_TYPES = (
    AttributeType.INTEGER,
    AttributeType.DECIMAL,
    AttributeType.BOOLEAN,
    AttributeType.TIMEDELTA,
)

ATTRIBUTE_DATETIME_TYPES = (
    AttributeType.DATETIME,
    AttributeType.DATE,
)


class AttributeQuerySet(TranslatableQuerySet):
    def visible(self):
        return self.exclude(visibility_mode=AttributeVisibility.HIDDEN)


@python_2_unicode_compatible
class Attribute(TranslatableModel):
    identifier = InternalIdentifierField(unique=True, blank=False, null=False, editable=True)
    searchable = models.BooleanField(default=True, verbose_name=_("searchable"), help_text=_(
        "Searchable attributes will be used for product lookup when customers search your store."
    ))
    type = EnumIntegerField(
        AttributeType, default=AttributeType.TRANSLATED_STRING, verbose_name=_("type"), help_text=_(
            "The attribute data type. Attribute values can be set on the product editor page."
        ))
    visibility_mode = EnumIntegerField(
        AttributeVisibility,
        default=AttributeVisibility.SHOW_ON_PRODUCT_PAGE,
        verbose_name=_("visibility mode"),
        help_text=_(
            "Select the attribute visibility setting. "
            "Attributes can be shown on the product detail page or can be used to enhance product search results."))

    translations = TranslatedFields(
        name=models.CharField(max_length=64, verbose_name=_("name"), help_text=_(
            "The attribute name. "
            "Product attributes can be used to list the various features of a product and can be shown on the "
            "product detail page. The product attributes for a product are determined by the product type and can "
            "be set on the product editor page."
        )),
    )

    objects = AttributeQuerySet.as_manager()

    class Meta:
        verbose_name = _('attribute')
        verbose_name_plural = _('attributes')

    def __str__(self):
        return u'%s' % self.name

    def save(self, *args, **kwargs):
        if not self.identifier:
            raise ValueError(u"Attribute with null identifier not allowed")
        self.identifier = flatten(("%s" % self.identifier).lower())
        return super(Attribute, self).save(*args, **kwargs)

    def formfield(self, **kwargs):
        """
        Get a form field for this attribute.

        :param kwargs: Kwargs to pass for the form field class.
        :return: Form field.
        :rtype: forms.Field
        """
        kwargs.setdefault("required", False)
        kwargs.setdefault("label", self.safe_translation_getter("name", self.identifier))
        if self.type == AttributeType.INTEGER:
            return forms.IntegerField(**kwargs)
        elif self.type == AttributeType.DECIMAL:
            return forms.DecimalField(**kwargs)
        elif self.type == AttributeType.BOOLEAN:
            return forms.NullBooleanField(**kwargs)
        elif self.type == AttributeType.TIMEDELTA:
            kwargs.setdefault("help_text", "(as seconds)")
            # TODO: This should be more user friendly
            return forms.DecimalField(**kwargs)
        elif self.type == AttributeType.DATETIME:
            return forms.DateTimeField(**kwargs)
        elif self.type == AttributeType.DATE:
            return forms.DateField(**kwargs)
        elif self.type == AttributeType.UNTRANSLATED_STRING:
            return forms.CharField(**kwargs)
        elif self.type == AttributeType.TRANSLATED_STRING:
            # Note: this isn't enough for actually saving multi-language entries;
            #       the caller will have to deal with calling this function several
            #       times for that.
            return forms.CharField(**kwargs)
        else:
            raise ValueError("`formfield` can't deal with fields of type %r" % self.type)

    @property
    def is_translated(self):
        return (self.type == AttributeType.TRANSLATED_STRING)

    @property
    def is_stringy(self):
        # Pun intended.
        return (self.type in ATTRIBUTE_STRING_TYPES)

    @property
    def is_numeric(self):
        return (self.type in ATTRIBUTE_NUMERIC_TYPES)

    @property
    def is_temporal(self):
        return (self.type in ATTRIBUTE_DATETIME_TYPES)

    def is_null_value(self, value):
        """
        Find out whether the given value is null from this attribute's point of view.

        :param value: A value
        :type value: object
        :return: Nulliness boolean
        :rtype: bool
        """
        if self.type == AttributeType.BOOLEAN:
            return (value is None)
        return (not value)


class AppliedAttribute(TranslatableModel):
    _applied_fk_field = None  # Used by the `repr` implementation

    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, verbose_name=_("attribute"))

    numeric_value = models.DecimalField(
        null=True, blank=True, max_digits=36, decimal_places=9, verbose_name=_("numeric value"), db_index=True)
    datetime_value = models.DateTimeField(
        auto_now_add=False, editable=True, null=True, blank=True, verbose_name=_("datetime value"), db_index=True)
    untranslated_string_value = models.TextField(blank=True, verbose_name=_("untranslated value"))

    # Concrete subclasses will require this TranslatedFields declaration:
    # translations = TranslatedFields(
    #     translated_string_value=models.TextField(blank=True),
    # )

    class Meta:
        abstract = True

    def _get_value(self):
        if self.attribute.type == AttributeType.BOOLEAN:
            """
            Return Boolean value or None

            Since we are using ``django.forms.fields.NullBooleanField`` in admin
            we should return either None, True or False.

            While the `Unknown` option (`None`) will never end up in the database
            when product attribute is being saved in admin, it is possible to
            create this value through API and that causes admin to break.
            """
            return bool(int(self.numeric_value)) if self.numeric_value is not None else None

        if self.attribute.type == AttributeType.INTEGER:
            return int(self.numeric_value)

        if self.attribute.type == AttributeType.DECIMAL:
            return Decimal(self.numeric_value)

        if self.attribute.type == AttributeType.TIMEDELTA:
            return datetime.timedelta(seconds=float(self.numeric_value))

        if self.attribute.type == AttributeType.DATETIME:
            return self.datetime_value

        if self.attribute.type == AttributeType.DATE:
            return self.datetime_value.date()

        if self.attribute.type == AttributeType.UNTRANSLATED_STRING:
            return self.untranslated_string_value

        if self.attribute.type == AttributeType.TRANSLATED_STRING:
            if self.has_translation():
                return self.translated_string_value
            return u""

        raise ValueError("Unknown attribute type.")  # pragma: no cover

    def _set_numeric_value(self, new_value):
        if self.attribute.type == AttributeType.BOOLEAN and new_value is None:
            """
            Shuup uses `django.forms.fields.NullBooleanField` in admin.
            Which can read in the `None` value.

            Note: This is being handled separately due backwards compatibility.
            TODO (2.0): Boolean should not be a special case and handling `None` should be
            same for every "numeric" value.
            """
            self.numeric_value = None
            self.datetime_value = None
            self.untranslated_string_value = ""
            return

        if isinstance(new_value, datetime.timedelta):
            value = new_value.total_seconds()
            if value == int(value):
                value = int(value)
        else:
            value = parse_decimal_string(new_value or 0)

        if self.attribute.type == AttributeType.INTEGER:
            value = int(value)

        if self.attribute.type == AttributeType.BOOLEAN:
            value = int(bool(value))

        self.numeric_value = value
        self.datetime_value = None
        self.untranslated_string_value = str(self.numeric_value)
        return

    def _set_string_value(self, new_value):
        if new_value is None:
            new_value = ""
        new_value = six.text_type(new_value)

        if self.attribute.type == AttributeType.UNTRANSLATED_STRING:
            self.untranslated_string_value = new_value
        elif self.attribute.type == AttributeType.TRANSLATED_STRING:
            self.translated_string_value = new_value
        try:
            self.numeric_value = int(self.string_value, 10)
        except:
            self.numeric_value = None
        self.datetime_value = None
        return

    def _set_datetime_value(self, new_value):
        if self.attribute.type == AttributeType.DATETIME:
            # Just store datetimes
            if not isinstance(new_value, datetime.datetime):
                raise TypeError("Can't assign %r to DATETIME attribute" % new_value)
            self.datetime_value = new_value
            self.numeric_value = calendar.timegm(self.datetime_value.timetuple())
            self.untranslated_string_value = self.datetime_value.isoformat()
        elif self.attribute.type == AttributeType.DATE:
            # Store dates as "date at midnight"
            date = parse_date(new_value)
            self.datetime_value = datetime.datetime.combine(date=date, time=datetime.time())
            self.numeric_value = date.toordinal()  # Store date ordinal as numeric value
            self.untranslated_string_value = date.isoformat()  # Store date ISO format as string value

    def _set_value(self, new_value):
        if self.attribute.is_numeric:
            self._set_numeric_value(new_value)
            return

        if self.attribute.is_stringy:
            self._set_string_value(new_value)
            return

        if self.attribute.is_temporal:
            self._set_datetime_value(new_value)
            return

        raise ValueError("Unknown attribute type.")  # pragma: no cover

    value = property(_get_value, _set_value)

    @property
    def name(self):
        """
        Get the name of the underlying attribute in the current language.
        """
        return self.attribute.safe_translation_getter("name", self.attribute.identifier)

    @property
    def formatted_value(self):
        """
        Get a human-consumable value for the attribute.

        The current locale is used for formatting.

        :return: Textual value
        :rtype: str
        """
        try:
            if self.attribute.type == AttributeType.BOOLEAN:
                return yesno(self.value)
            if self.attribute.type in (AttributeType.INTEGER, AttributeType.DECIMAL):
                return format_number(self.value)
            if self.attribute.type == AttributeType.TIMEDELTA:
                a = now()
                b = a + self.value
                return timesince(a, b)
            if self.attribute.type in (AttributeType.DATETIME, AttributeType.DATE):
                return format_datetime(self.value)
        except:  # If formatting fails, fall back to string formatting.
            pass
        return six.text_type(self.value)

    def __repr__(self):  # pragma: no cover
        return '<%s of %r: %s=%r>' % (
            type(self).__name__,
            getattr(self, self._applied_fk_field or "", None),
            self.attribute.identifier,
            self.value
        )


class AttributableMixin(object):

    def _set_cached_attribute(self, language, identifier, applied_attribute):
        if not hasattr(self, "_attr_cache"):
            self._attr_cache = {}
        self._attr_cache[(language, identifier or applied_attribute.attribute.identifier)] = applied_attribute

    @classmethod
    def cache_attributes_for_targets(
            cls, applied_attr_cls, targets, attribute_identifiers, language):
        if not settings.SHUUP_ENABLE_ATTRIBUTES:  # pragma: no cover
            return targets

        applied_attrs_by_target_id = defaultdict(list)
        attr_ids = set()
        filter_kwargs = {
            "%s_id__in" % (applied_attr_cls._applied_fk_field): (t.pk for t in targets),
            "attribute__identifier__in": attribute_identifiers
        }

        for applied_attr in applied_attr_cls.objects.language(language).filter(**filter_kwargs):
            attr_ids.add(applied_attr.attribute_id)
            applied_attrs_by_target_id[applied_attr.product_id].append(applied_attr)
        attr_map = dict((attr.id, attr) for attr in Attribute.objects.language(language).filter(id__in=attr_ids))

        for target in targets:
            for identifier in attribute_identifiers:
                target._set_cached_attribute(language, identifier, NoSuchAttributeHere)

            for applied_attr in applied_attrs_by_target_id.get(target.id, ()):
                attribute_descriptor = applied_attr.__class__.attribute
                setattr(applied_attr, attribute_descriptor.cache_name, attr_map.get(applied_attr.attribute_id))
                target._set_cached_attribute(language, applied_attr.attribute.identifier, applied_attr)

        return targets

    def get_available_attribute_queryset(self):  # pragma: no cover
        raise NotImplementedError("Must be implemented in AttributableMixin subclass")

    def get_all_attribute_info(self, language=None, visibility_mode=None):
        if not settings.SHUUP_ENABLE_ATTRIBUTES:  # pragma: no cover
            return {}

        language = language or get_language()
        qs = self.get_available_attribute_queryset().language(language).all()

        if visibility_mode is not None:
            qs = qs.filter(visibility_mode=visibility_mode)

        all_attributes = dict((a.identifier, (a, None)) for a in qs)

        applied_attribute_qs = self.attributes.all().select_related("attribute")
        if visibility_mode is not None:
            applied_attribute_qs = applied_attribute_qs.filter(attribute__visibility_mode=visibility_mode)

        existing_attributes = dict(
            (aa.attribute.identifier, (all_attributes.get(aa.attribute.identifier, (aa.attribute,))[0], aa))
            for aa in applied_attribute_qs
        )

        attribute_infos = {}
        attribute_infos.update(all_attributes)
        attribute_infos.update(existing_attributes)
        return attribute_infos

    def clear_attribute_cache(self):
        if hasattr(self, "_attr_cache"):
            del self._attr_cache

    def get_attribute_value(self, identifier, language=None, default=None):
        """
        Get the value of the attribute with the identifier string `identifier`
        in the given (or current) language.

        If the attribute is not found, return `default`.

        :param identifier: Attribute identifier
        :type identifier: str
        :param language: Language identifier (or `None` for "current")
        :type language: str|None
        :param default: Default value to return
        :type default: object
        :return: Attribute value (or fallback)
        :rtype: object
        """
        if not settings.SHUUP_ENABLE_ATTRIBUTES:  # pragma: no cover
            return ""

        language = language or get_language()

        applied_attr = None

        _attr_cache = getattr(self, "_attr_cache", {})

        if _attr_cache:
            applied_attr = _attr_cache.get((language, identifier))
            if applied_attr is NoSuchAttributeHere:  # pragma: no cover
                # cache warmed but value was not found
                return default

        if applied_attr is None:
            try:
                applied_attr = (
                    self.attributes.language(language).select_related("attribute")
                    .get(attribute__identifier=identifier)
                )
            except ObjectDoesNotExist:
                applied_attr = None

            if applied_attr:
                self._set_cached_attribute(language, applied_attr.attribute.identifier, applied_attr)
            else:  # Cache the miss
                self._set_cached_attribute(language, identifier, NoSuchAttributeHere)

        if applied_attr:
            return applied_attr.value
        return default

    def set_attribute_value(self, identifier, value, language=None):
        """
        Set an attribute value.

        :param identifier: Attribute identifier
        :type identifier: str
        :param value: The value for the attribute (should be in the correct type for the attribute).
        :type value: object
        :param language: Language for multi-language attributes. Not required for untranslated attributes.
        :type language: str
        :return: Applied attribute object or None
        :rtype: AppliedAttribute|None
        """
        if not settings.SHUUP_ENABLE_ATTRIBUTES:  # pragma: no cover
            return

        attr = self.get_available_attribute_queryset().get(identifier=identifier)
        applied_attr = self.attributes.filter(attribute=attr).first()

        if not applied_attr:
            applied_attr = self.attributes.model(attribute=attr)
            setattr(applied_attr, applied_attr._applied_fk_field, self)
        else:
            self.clear_attribute_cache()

        if attr.is_translated:
            if not language:
                raise ValueError("`language` must be set for translated attribute %s" % attr)
            applied_attr.set_current_language(language)

        if not attr.is_translated and attr.is_null_value(value):
            # Trying to set a null value for an untranslated attribute,
            # so we can just get rid of the applied object altogether.
            # TODO: Do the same sort of cleanup for translated attributes.
            if applied_attr.pk:
                applied_attr.delete()
            return

        # Set the value and save the attribute (possibly new)
        applied_attr.value = value
        applied_attr.save()
        return applied_attr

    def clear_attribute_value(self, identifier, language=None):
        avail_attrs = self.get_available_attribute_queryset()
        attr = avail_attrs.get(identifier=identifier)
        attr_val = self.attributes.filter(attribute=attr).first()
        if not attr_val:
            return
        if language is None:  # Delete all translations
            attr_val.delete()
            return
        trans = attr_val.translations.filter(language_code=language).first()
        if trans:
            trans.delete()


AttributeLogEntry = define_log_model(Attribute)
