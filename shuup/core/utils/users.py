# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail.message import EmailMessage
from django.template import loader
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from six.moves.urllib.parse import urljoin

from shuup import configuration
from shuup.core.signals import user_reset_password_requested
from shuup.utils.django_compat import is_anonymous

ALL_SEEING_FORMAT = "is_all_seeing:%(user_id)s"
FORCE_ANONYMOYS_FORMAT = "force_anonymous_contact:%(user_id)s"
FORCE_PERSON_FORMAT = "force_person_contact:%(user_id)s"


def real_user_or_none(user):
    """
    Convert anonymous user to None.

    If user is anonymous, return None, otherwise return the user as is.
    """
    assert (user is None or is_anonymous(user) or
            isinstance(user, get_user_model()))
    return user if (user and not is_anonymous(user)) else None


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


def send_user_reset_password_email(user, shop, reset_domain_url, reset_url_name,
                                   token_generator=None, subject_template_name=None,
                                   email_template_name=None, from_email=None):

    # trigger the signal
    handlers = user_reset_password_requested.send(
        sender=type(user),
        shop=shop,
        user=user,
        reset_domain_url=reset_domain_url,
        reset_url_name=reset_url_name
    )
    # from the registered handlers, check those which
    # properly handled the signal
    handlers_results = [handler[1] for handler in handlers]

    # no handler actually handled the signal, fallback to manual email template
    if not any(handlers_results) and token_generator and subject_template_name and email_template_name:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        recovery_url = urljoin(
            reset_domain_url,
            reverse(reset_url_name, kwargs=dict(uidb64=uid, token=token))
        )
        context = {
            'site_name': shop.public_name,
            'uid': uid,
            'user_to_recover': user,
            'token': token,
            'recovery_url': recovery_url
        }
        subject = loader.render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())  # Email subject *must not* contain newlines
        body = loader.render_to_string(email_template_name, context)
        email = EmailMessage(from_email=from_email, subject=subject, body=body, to=[user.email])
        email.content_subtype = settings.SHUUP_AUTH_EMAIL_CONTENT_SUBTYPE
        email.send()
