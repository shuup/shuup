# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os

import django

from shuup.addons import add_enabled_addons

BASE_DIR = os.getenv("SHUUP_WORKBENCH_BASE_DIR") or (
    os.path.dirname(os.path.dirname(__file__)))
SECRET_KEY = "Shhhhh"
DEBUG = True
ALLOWED_HOSTS = ["*"]

MEDIA_ROOT = os.path.join(BASE_DIR, "var", "media")
STATIC_ROOT = os.path.join(BASE_DIR, "var", "static")
MEDIA_URL = "/media/"

SHUUP_ENABLED_ADDONS_FILE = os.getenv("SHUUP_ENABLED_ADDONS_FILE") or (
    os.path.join(BASE_DIR, "var", "enabled_addons"))

INSTALLED_APPS = add_enabled_addons(SHUUP_ENABLED_ADDONS_FILE, [
    # django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    # external apps that needs to be loaded before Shuup
    'easy_thumbnails',
    # shuup themes
    'shuup.themes.classic_gray',
    # shuup
    'shuup.core',
    'shuup.admin',
    'shuup.addons',
    'shuup.default_tax',
    'shuup.front',
    'shuup.front.apps.auth',
    'shuup.front.apps.carousel',
    'shuup.front.apps.customer_information',
    'shuup.front.apps.personal_order_history',
    'shuup.front.apps.saved_carts',
    'shuup.front.apps.registration',
    'shuup.front.apps.simple_order_notification',
    'shuup.front.apps.simple_search',
    'shuup.front.apps.recently_viewed_products',
    'shuup.notify',
    'shuup.simple_cms',
    'shuup.customer_group_pricing',
    'shuup.campaigns',
    'shuup.simple_supplier',
    'shuup.order_printouts',
    'shuup.utils',
    'shuup.xtheme',
    'shuup.reports',
    'shuup.default_reports',
    'shuup.regions',
    'shuup.importer',
    'shuup.default_importer',
    'shuup.gdpr',
    'shuup.tasks',
    'shuup.discounts',

    # external apps
    'bootstrap3',
    'django_countries',
    'django_jinja',
    'django_filters',
    'filer',
    'reversion',
    'registration',
    'rest_framework',
])

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'shuup.front.middleware.ProblemMiddleware',
    'shuup.core.middleware.ShuupMiddleware',
    'shuup.front.middleware.ShuupFrontMiddleware',
    'shuup.xtheme.middleware.XthemeMiddleware',
    'shuup.admin.middleware.ShuupAdminMiddleware'
]

if django.VERSION < (2, 0):
    MIDDLEWARE_CLASSES = [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'shuup.front.middleware.ProblemMiddleware',
        'shuup.core.middleware.ShuupMiddleware',
        'shuup.front.middleware.ShuupFrontMiddleware',
        'shuup.xtheme.middleware.XthemeMiddleware',
        'shuup.admin.middleware.ShuupAdminMiddleware'
    ]


ROOT_URLCONF = 'shuup_workbench.urls'
WSGI_APPLICATION = 'shuup_workbench.wsgi.application'

_sqlite_folder = os.path.join(BASE_DIR, '../.sqlite')
if not os.path.exists(_sqlite_folder):
    os.mkdir(_sqlite_folder)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(_sqlite_folder, 'db.sqlite3'),
    }
}

LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'
LOGIN_REDIRECT_URL = '/'
SOUTH_TESTS_MIGRATE = False  # Makes tests that much faster.
DEFAULT_FROM_EMAIL = 'no-reply@example.com'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {'format': '[%(asctime)s] (%(name)s:%(levelname)s): %(message)s'},
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'shuup': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': True},
    }
}

LANGUAGES = [
    # List all supported languages here.
    #
    # Should be a subset of django.conf.global_settings.LANGUAGES.  Use
    # same spelling for the language names for utilizing the language
    # name translations from Django.
    ('en', 'English'),
    ('fi', 'Finnish'),
    ('it', 'Italian'),
    ('ja', 'Japanese'),
    ('pt-br', 'Brazilian Portuguese'),
    ('ru', 'Russian'),
    ('sv', 'Swedish'),
    ('zh-hans', 'Simplified Chinese'),
]

PARLER_DEFAULT_LANGUAGE_CODE = "en"

PARLER_LANGUAGES = {
    None: [{"code": c, "name": n} for (c, n) in LANGUAGES],
    'default': {
        'hide_untranslated': False,
    }
}

_TEMPLATE_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    "django.template.context_processors.debug",
    "django.template.context_processors.i18n",
    "django.template.context_processors.media",
    "django.template.context_processors.static",
    "django.template.context_processors.request",
    "django.template.context_processors.tz",
    "django.contrib.messages.context_processors.messages"
]

TEMPLATES = [
    {
        "BACKEND": "django_jinja.backend.Jinja2",
        "APP_DIRS": True,
        "OPTIONS": {
            "match_extension": ".jinja",
            "context_processors": _TEMPLATE_CONTEXT_PROCESSORS,
            "newstyle_gettext": True,
            "environment": "shuup.xtheme.engine.XthemeEnvironment",
        },
        "NAME": "jinja2",
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": _TEMPLATE_CONTEXT_PROCESSORS,
            "debug": DEBUG
        }
    },
]

# set login url here because of `login_required` decorators
LOGIN_URL = "/login/"

SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"

SHUUP_PRICING_MODULE = "customer_group_pricing"

SHUUP_SETUP_WIZARD_PANE_SPEC = [
    "shuup.admin.modules.shops.views:ShopWizardPane",
    "shuup.admin.modules.service_providers.views.PaymentWizardPane",
    "shuup.admin.modules.service_providers.views.CarrierWizardPane",
    "shuup.xtheme.admin_module.views.ThemeWizardPane",
    "shuup.testing.modules.sample_data.views.SampleObjectsWizardPane" if DEBUG else "",
    "shuup.admin.modules.system.views.TelemetryWizardPane"
]


SHUUP_ERROR_PAGE_HANDLERS_SPEC = [
    "shuup.admin.error_handlers:AdminPageErrorHandler",
    "shuup.front.error_handlers:FrontPageErrorHandler"
]

SHUUP_SIMPLE_SEARCH_LIMIT = 150

if os.environ.get("SHUUP_WORKBENCH_DISABLE_MIGRATIONS") == "1":
    from .utils import get_disabled_migrations
    MIGRATION_MODULES = get_disabled_migrations()


def configure(setup):
    setup.commit(globals())
