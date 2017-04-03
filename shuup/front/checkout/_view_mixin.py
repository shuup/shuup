# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import reverse

from shuup.front.basket import get_basket
from shuup.front.basket.objects import BaseBasket

from ._storage import CheckoutPhaseStorage


class CheckoutPhaseViewMixin(object):
    identifier = None
    title = None  # User-visible
    final = False  # Should be set for final steps (those that may be accessed via the previous step's URL)

    horizontal_template = True  # Set this to False if you want to use single page checkout

    checkout_process = None  # set as an instance variable
    phases = ()  # set as an instance variable; likely accessed via template (`view.phases`)
    next_phase = None  # set as an instance variable
    previous_phase = None  # set as an instance variable
    request = None  # exists via being a view

    basket_class = BaseBasket
    basket_name_attr = "basket"

    def is_visible_for_user(self):
        return bool(self.title)

    def is_valid(self):
        return True

    def should_skip(self):
        return False

    def process(self):
        raise NotImplementedError("`process` MUST be overridden in %r" % self.__class__)

    def reset(self):
        self.storage.reset()

    def get_success_url(self, *args, **kwargs):
        if self.next_phase:
            return reverse("shuup:checkout", kwargs={"phase": self.next_phase.identifier})
        next_obj = super(CheckoutPhaseViewMixin, self)
        if hasattr(next_obj, 'get_success_url'):
            return next_obj.get_success_url(*args, **kwargs)

    def get_url(self, request):
        return reverse("shuup:checkout", kwargs={"phase": self.identifier})

    @property
    def basket(self):
        """
        :rtype: BaseBasket
        :return:
        """
        return self._get_basket_from_request(self.request)

    @property
    def storage(self):
        if not hasattr(self, "_storage"):
            self._storage = CheckoutPhaseStorage(request=self.request, phase_identifier=self.identifier)
        return self._storage

    def _get_basket_from_request(self, request):

        """
        :rtype: BaseBasket
        :return:
        """
        if not hasattr(request, self.basket_name_attr):
            _basket = get_basket(request, basket_name=self.basket_name_attr, basket_class=self.basket_class)
            setattr(request, self.basket_name_attr, _basket)
        return getattr(request, self.basket_name_attr)

    def get_context_data(self, **kwargs):
        context = super(CheckoutPhaseViewMixin, self).get_context_data(**kwargs)
        context["current_phase_url"] = self.get_url(self.request)
        context["next_phase_url"] = self.next_phase.get_url(self.request) if self.next_phase else None
        context["previous_phase_url"] = self.previous_phase.get_url(self.request) if self.previous_phase else None

        # build phase urls
        urls = {}
        for phase in self.phases:
            urls[phase.identifier] = phase.get_url(self.request)
        context["phase_urls"] = urls

        return context
