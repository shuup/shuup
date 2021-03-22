# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
import itertools
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import activate

from shuup.admin.forms.fields import WeekdayField
from shuup.campaigns.models import CatalogCampaign
from shuup.campaigns.models.catalog_filters import CategoryFilter, ProductFilter
from shuup.campaigns.models.context_conditions import ContactCondition, ContactGroupCondition, HourCondition
from shuup.campaigns.models.product_effects import ProductDiscountAmount, ProductDiscountPercentage
from shuup.core.models import Category, CompanyContact, ContactGroup, PersonContact, Product
from shuup.discounts.models import Discount, HappyHour, TimeRange


class Command(BaseCommand):
    def handle(self, *args, **options):
        activate(settings.PARLER_DEFAULT_LANGUAGE_CODE)

        Discount.objects.all().delete()
        HappyHour.objects.all().delete()
        for campaign in CatalogCampaign.objects.all():
            data, categories, contact_groups, contacts, products, happy_hours = _get_data_from_campaign(campaign)
            new_happy_hours = []
            for happy_hour_name, time_ranges in happy_hours:
                happy_hour = HappyHour.objects.create(name=happy_hour_name)
                happy_hour.shops.set([campaign.shop])
                happy_hour.time_ranges.all().delete()

                possible_parent = None
                for valid_hour in time_ranges:
                    valid_hour.update({"happy_hour": happy_hour})
                    if possible_parent and valid_hour.get("continuation", False):
                        valid_hour.pop("continuation")
                        valid_hour.update({"parent": possible_parent})

                    possible_parent = TimeRange.objects.create(**valid_hour)

                new_happy_hours.append(happy_hour)

            conditions = [categories, contact_groups, products, contacts]
            conditions_trimmed = [condition_list for condition_list in conditions if len(condition_list)]
            for condition_items in itertools.product(*conditions_trimmed):
                product, category, contact, contact_group = _open_condition_items(condition_items)

                identifier = "catalog_campaign-%s-%s-%s-%s-%s" % (
                    campaign.pk,
                    product.pk if product else 0,
                    category.pk if category else 0,
                    contact.pk if contact else 0,
                    contact_group.pk if contact_group else 0,
                )
                data.update(
                    {"product": product, "category": category, "contact": contact, "contact_group": contact_group}
                )

                discount, created = Discount.objects.get_or_create(identifier=identifier, defaults=data)
                discount.shops.set([campaign.shop])
                discount.happy_hours.set(new_happy_hours)


def _get_data_from_campaign(campaign):  # noqa
    data = {
        "created_by": campaign.created_by,
        "active": campaign.active,
        "start_datetime": campaign.start_datetime,
        "end_datetime": campaign.end_datetime,
    }
    categories = []
    contact_groups = []
    contacts = []
    products = []
    happy_hours = []

    for condition in campaign.conditions.all():
        if isinstance(condition, ContactCondition):
            contacts = condition.contacts.all()
        elif isinstance(condition, ContactGroupCondition):
            contact_groups = condition.contact_groups.all()
        elif isinstance(condition, HourCondition):
            time_ranges = []
            for valid_day in condition.days.split(","):
                if condition.hour_end < condition.hour_start:
                    time_ranges.append(
                        {
                            "from_hour": condition.hour_start,
                            "to_hour": datetime.time(hour=23, minute=59),
                            "weekday": int(valid_day),
                        }
                    )
                    time_ranges.append(
                        {
                            "continuation": True,
                            "from_hour": datetime.time(hour=0),
                            "to_hour": condition.hour_end,
                            "weekday": (int(valid_day) + 1 if int(valid_day) < 6 else 0),
                        }
                    )
                else:
                    time_ranges.append(
                        {"from_hour": condition.hour_start, "to_hour": condition.hour_end, "weekday": int(valid_day)}
                    )

            happy_hours.append(
                (
                    "%s %s-%s" % (_get_weekdays_in_labels(condition.days), condition.hour_start, condition.hour_end),
                    time_ranges,
                )
            )

    for filter in campaign.filters.all():
        if isinstance(filter, ProductFilter):
            products = filter.products.all()
        elif isinstance(filter, CategoryFilter):
            categories = filter.categories.all()

    for effect in campaign.effects.all():
        if isinstance(effect, ProductDiscountAmount):
            data.update({"discount_amount_value": effect.discount_amount})
        elif isinstance(effect, ProductDiscountPercentage):
            data.update({"discount_percentage": effect.discount_percentage})

    return data, categories, contact_groups, contacts, products, happy_hours


def _get_weekdays_in_labels(weekdays):
    return ", ".join(["%s" % label for value, label in WeekdayField.DAYS_OF_THE_WEEK if "%s" % value in weekdays])


def _open_condition_items(condition_items):
    product = None
    category = None
    contact = None
    contact_group = None

    for condition in condition_items:
        if isinstance(condition, Product):
            product = condition

        if isinstance(condition, Category):
            category = condition

        if isinstance(condition, PersonContact) or isinstance(condition, CompanyContact):
            contact = condition

        if isinstance(condition, ContactGroup):
            contact_group = condition

    return product, category, contact, contact_group
