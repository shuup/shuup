# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth import get_user_model

from shuup import configuration

ALL_SEEING_FORMAT = "is_all_seeing:%(user_id)s"
FORCE_ANONYMOYS_FORMAT = "force_anonymous_contact:%(user_id)s"
FORCE_PERSON_FORMAT = "force_person_contact:%(user_id)s"


def real_user_or_none(user):
    """
    Convert anonymous user to None.

    If user is anonymous, return None, otherwise return the user as is.
    """
    assert (user is None or user.is_anonymous() or
            isinstance(user, get_user_model()))
    return user if (user and not user.is_anonymous()) else None


def toggle_all_seeing_for_user(user):
    if not getattr(user, "is_superuser", False):
        return

    all_seeing_key = ALL_SEEING_FORMAT % {"user_id": user.pk}
    is_all_seeing = configuration.get(None, all_seeing_key, False)
    configuration.set(None, all_seeing_key, not is_all_seeing)


def is_user_all_seeing(user):
    if user and user.pk and getattr(user, "is_superuser", False):
        return configuration.get(None, ALL_SEEING_FORMAT % {"user_id": user.pk}, False)
    return False


def should_force_anonymous_contact(user):
    return configuration.get(None, FORCE_ANONYMOYS_FORMAT % {"user_id": user.pk}, False)


def should_force_person_contact(user):
    return configuration.get(None, FORCE_PERSON_FORMAT % {"user_id": user.pk}, False)


def force_anonymous_contact_for_user(user, value=True):
    configuration.set(None, FORCE_ANONYMOYS_FORMAT % {"user_id": user.pk}, value)


def force_person_contact_for_user(user, value=True):
    configuration.set(None, FORCE_PERSON_FORMAT % {"user_id": user.pk}, value)
