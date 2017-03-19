# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.template import loader
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from shuup.core.middleware import ExceptionMiddleware
from shuup.core.models import (
    Contact, get_company_contact, get_person_contact, Shop
)
from shuup.front.basket import get_basket

__all__ = ["ProblemMiddleware", "ShuupFrontMiddleware"]

ProblemMiddleware = ExceptionMiddleware  # This class is only an alias for ExceptionMiddleware.


class ShuupFrontMiddleware(object):
    """
    Handle Shuup specific tasks for each request and response.

    * Set request attributes that rest of the Shuup front-end rely on.

    * Set Django's timezone according to personal preferences
      (i.e. request.person.timezone).

      .. TODO:: Fallback to shop timezone?

    * Make sure that basket is saved before response is returned to the
      browser.

    Attributes set for requests:

      ``request.shop`` : :class:`shuup.core.models.Shop`
          Currently active Shop.

          .. TODO:: Define better

      ``request.person`` : :class:`shuup.core.models.Contact`
          :class:`~shuup.core.models.PersonContact` of currently logged
          in user or :class:`~shuup.core.models.AnonymousContact` if
          there is no logged in user.

      ``request.customer`` : :class:`shuup.core.models.Contact`
          Customer contact used when creating Orders.  This can be same
          as ``request.person``, but for example in B2B shops this is
          usually a :class:`~shuup.core.models.CompanyContact` whereas
          ``request.person`` is a
          :class:`~shuup.core.models.PersonContact`.

      ``request.basket`` : :class:`shuup.front.basket.objects.BaseBasket`
          Shopping basket in use.
    """

    def process_request(self, request):
        self._set_shop(request)
        self._set_person(request)
        self._set_customer(request)
        self._set_basket(request)
        self._set_timezone(request)
        self._set_price_display_options(request)

    def _set_shop(self, request):
        # TODO: Not the best logic :)
        request.shop = Shop.objects.first()
        if not request.shop:
            raise ImproperlyConfigured("No shop!")

    def _set_person(self, request):
        request.person = get_person_contact(request.user)
        if not request.person.is_active:
            messages.add_message(request, messages.INFO, _("Logged out since this account is inactive."))
            logout(request)
            # Usually logout is connected to the `refresh_on_logout`
            # method via a signal and that already sets request.person
            # to anonymous, but set it explicitly too, just to be sure
            request.person = get_person_contact(None)

    def _set_customer(self, request):
        company = get_company_contact(request.user)
        request.customer = (company or request.person)
        request.is_company_member = bool(company)
        request.customer_groups = (company or request.person).groups.all()

    def _set_basket(self, request):
        request.basket = get_basket(request)

    def _set_timezone(self, request):
        if request.person.timezone:
            timezone.activate(request.person.timezone)
            # TODO: Fallback to request.shop.timezone (and add such field)

    def _set_price_display_options(self, request):
        customer = request.customer
        assert isinstance(customer, Contact)
        customer.get_price_display_options().set_for_request(request)

    def process_response(self, request, response):
        if hasattr(request, "basket") and request.basket.dirty:
            request.basket.save()

        return response

    @classmethod
    def refresh_on_user_change(cls, request, user=None, **kwargs):
        # In some cases, there is no `user` attribute in
        # the request, which would cause the middleware to fail.
        # If that's the case, let's assign the freshly changed user
        # now.
        if not hasattr(request, "user"):
            request.user = user
        cls().process_request(request)

    @classmethod
    def refresh_on_logout(cls, request, **kwargs):
        # The `user_logged_out` signal is fired _before_ `request.user` is set to `AnonymousUser()`,
        # so we'll have to do switcharoos and hijinks before invoking `refresh_on_user_change`.

        # The `try: finally:` is there to ensure other signal consumers still get an unchanged (well,
        # aside from `.person` etc. of course) `request` to toy with.

        # Oh, and let's also add shenanigans to switcharoos and hijinks. Shenanigans.

        current_user = getattr(request, "user", None)
        try:
            request.user = AnonymousUser()
            cls.refresh_on_user_change(request)
        finally:
            request.user = current_user

    def process_view(self, request, view_func, *view_args, **view_kwargs):
        maintenance_response = self._get_maintenance_response(request, view_func)
        if maintenance_response:
            return maintenance_response

    def _get_maintenance_response(self, request, view_func):
        if settings.DEBUG:
            # Allow media and static accesses in debug mode
            if request.path.startswith("/media") or request.path.startswith("/static"):
                return None
        if getattr(view_func, "maintenance_mode_exempt", False):
            return None
        if "login" in view_func.__name__:
            return None
        resolver_match = getattr(request, "resolver_match", None)
        if resolver_match and resolver_match.app_name == "shuup_admin":
            return None

        if request.shop.maintenance_mode and not getattr(request.user, 'is_superuser', False):
            return HttpResponse(loader.render_to_string("shuup/front/maintenance.jinja", request=request), status=503)


if (
    "django.contrib.auth" in settings.INSTALLED_APPS and
    "shuup.front.middleware.ShuupFrontMiddleware" in settings.MIDDLEWARE_CLASSES
):
    user_logged_in.connect(ShuupFrontMiddleware.refresh_on_user_change, dispatch_uid="shuup_front_refresh_on_login")
    user_logged_out.connect(ShuupFrontMiddleware.refresh_on_logout, dispatch_uid="shuup_front_refresh_on_logout")
