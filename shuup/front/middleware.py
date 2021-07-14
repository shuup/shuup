# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.http import HttpResponse
from django.template import loader
from django.utils import timezone, translation
from django.utils.translation import ugettext_lazy as _
from functools import lru_cache

from shuup.core.middleware import ExceptionMiddleware
from shuup.core.models import AnonymousContact, Contact, get_company_contact, get_person_contact
from shuup.core.shop_provider import get_shop
from shuup.core.utils.users import should_force_anonymous_contact, should_force_person_contact
from shuup.front.basket import get_basket
from shuup.front.utils.user import is_admin_user
from shuup.utils.django_compat import MiddlewareMixin, get_middleware_classes

__all__ = ["ProblemMiddleware", "ShuupFrontMiddleware"]

ProblemMiddleware = ExceptionMiddleware  # This class is only an alias for ExceptionMiddleware.


class ShuupFrontMiddleware(MiddlewareMixin):
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

      ``request.person`` : :class:`shuup.core.models.Contact`
          :class:`~shuup.core.models.PersonContact` of currently logged
          in user or :class:`~shuup.core.models.AnonymousContact` if
          there is no logged-in user.

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
        if settings.DEBUG and (
            request.path.startswith(settings.MEDIA_URL) or request.path.startswith(settings.STATIC_URL)
        ):
            return None

        self._set_shop(request)
        self._set_person(request)
        self._set_customer(request)
        self._set_basket(request)
        self._set_timezone(request)
        self._set_price_display_options(request)

    def _set_shop(self, request):
        """
        Set the shop here again, even if the ShuupCore already did it.
        As we use this middleware alone in `refresh_on_user_change`, we should ensure the request shop.
        """
        request.shop = get_shop(request)

    def _set_person(self, request):
        if should_force_anonymous_contact(request.user):
            request.person = AnonymousContact()
        else:
            request.person = get_person_contact(request.user)
            if not request.person.is_active:
                messages.add_message(request, messages.INFO, _("Logged out since this account is inactive."))
                logout(request)
                # Usually logout is connected to the `refresh_on_logout`
                # method via a signal and that already sets request.person
                # to anonymous. But set it explicitly too, just to be sure.
                request.person = get_person_contact(None)

    def _set_customer(self, request):
        if not request.person or should_force_person_contact(request.user):
            company = None
        else:
            company = get_company_contact(request.user)

        request.customer = company or request.person
        request.is_company_member = bool(company)
        request.customer_groups = (company or request.person).groups.all()

    def _set_basket(self, request):
        request.basket = get_basket(request)

    def _set_timezone(self, request):
        if request.person.timezone:
            timezone.activate(request.person.timezone)
        elif request.session.get("tz"):
            timezone.activate(request.session["tz"])

            if request.person:
                request.person.timezone = request.session["tz"]
                request.person.save(update_fields=["timezone"])

        else:
            timezone.activate(settings.TIME_ZONE)

        request.TIME_ZONE = timezone.get_current_timezone_name()

    def _set_price_display_options(self, request):
        customer = request.customer
        assert isinstance(customer, Contact)
        customer.get_price_display_options(shop=request.shop).set_for_request(request)

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

    @lru_cache()
    def _get_front_urlpatterns_callbacks(self):
        from shuup.front.urls import urlpatterns

        return [urlpattern.callback for urlpattern in urlpatterns]

    def process_view(self, request, view_func, *view_args, **view_kwargs):
        maintenance_response = self._get_maintenance_response(request, view_func)
        if maintenance_response:
            return maintenance_response

        # only force settings language when in Front urls
        if view_func in self._get_front_urlpatterns_callbacks():
            self._set_language(request)

    def _set_language(self, request):
        """
        Set the language according to the shop preferences.
        If the current language is not in the available ones, change it to the first available.
        """
        from shuup.front.utils.translation import get_language_choices

        current_language = translation.get_language()
        available_languages = [code for (code, name, local_name) in get_language_choices(request.shop)]
        if current_language not in available_languages:
            if available_languages:
                translation.activate(available_languages[0])
            else:
                # fallback to LANGUAGE_CODE
                translation.activate(settings.LANGUAGE_CODE)
            request.LANGUAGE_CODE = translation.get_language()

    def _get_maintenance_response(self, request, view_func):
        # Allow media and static accesses in debug mode
        if settings.DEBUG and (
            request.path.startswith(settings.MEDIA_URL) or request.path.startswith(settings.STATIC_URL)
        ):
            return None

        if getattr(view_func, "maintenance_mode_exempt", False):
            return None
        if "login" in view_func.__name__:
            return None
        resolver_match = getattr(request, "resolver_match", None)
        if resolver_match and resolver_match.app_name == "shuup_admin":
            return None

        if request.shop.maintenance_mode and not is_admin_user(request):
            return HttpResponse(loader.render_to_string("shuup/front/maintenance.jinja", request=request), status=503)


if (
    "django.contrib.auth" in settings.INSTALLED_APPS
    and "shuup.front.middleware.ShuupFrontMiddleware" in get_middleware_classes()
):
    user_logged_in.connect(ShuupFrontMiddleware.refresh_on_user_change, dispatch_uid="shuup_front_refresh_on_login")
    user_logged_out.connect(ShuupFrontMiddleware.refresh_on_logout, dispatch_uid="shuup_front_refresh_on_logout")
