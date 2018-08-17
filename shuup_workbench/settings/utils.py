# -*- coding: utf-8 -*-
import django


class DisableMigrations(object):
    # See https://gist.github.com/NotSqrt/5f3c76cd15e40ef62d09
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return "notmigrations"


def get_disabled_migrations():
    if django.VERSION < (1, 11):
        return DisableMigrations()

    return {
        'auth': None,
        'contenttypes': None,
        'default': None,
        'sessions': None,

        'shuup': None,
        'shuup_admin': None,
        'default_tax': None,
        'shuup_front': None,
        'carousel': None,
        'shuup_notify': None,
        'shuup_simple_cms': None,
        'simple_supplier': None,
        'shuup_customer_group_pricing': None,
        'campaigns': None,
        'shuup_xtheme': None,
        'shuup_testing': None,
        'shuup_gdpr': None,
        'shuup_tasks': None,
        'discounts': None,

        'django_countries': None,
        'filer': None,
        'reversion': None
    }
