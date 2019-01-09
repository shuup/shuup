# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import warnings

from ._process import CheckoutProcess
from ._storage import CheckoutPhaseStorage


class CheckoutPhaseViewMixin(object):
    identifier = None
    title = None  # User-visible
    final = False  # Should be set for final steps (those that may be accessed via the previous step's URL)

    phases = ()  # set as an instance variable; likely accessed via template (`view.phases`)
    next_phase = None  # set as an instance variable
    previous_phase = None  # set as an instance variable
    request = None  # exists via being a view

    def __init__(self, checkout_process=None, horizontal_template=True,
                 *args, **kwargs):
        """
        Initialize a checkout phase view.

        :type checkout_process: shuup.front.checkout.CheckoutProcess|None
        :param checkout_process: The checkout process of this phase

        :type horizontal_template: bool
        :param horizontal_template:
          Set this to False if you want to use single page checkout
        """
        # TODO: (2.0) Make checkout_process argument mandatory
        if not checkout_process:
            warnings.warn(
                "Using checkout view without a checkout process is deprecated",
                DeprecationWarning, 2)

        self._checkout_process = checkout_process
        self.horizontal_template = horizontal_template
        super(CheckoutPhaseViewMixin, self).__init__(*args, **kwargs)

    @property
    def checkout_process(self):
        """
        Get the checkout process of this phase.

        :rtype: shuup.front.checkout.CheckoutProcess
        """
        if not self._checkout_process:
            self._checkout_process = _get_dummy_checkout_process(self)
        return self._checkout_process

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
            return self.checkout_process.get_phase_url(self.next_phase)
        next_obj = super(CheckoutPhaseViewMixin, self)
        if hasattr(next_obj, 'get_success_url'):
            return next_obj.get_success_url(*args, **kwargs)

    def get_url(self):
        return self.checkout_process.get_phase_url(self)

    @property
    def basket(self):
        """
        The basket used in this checkout phase.

        :rtype: shuup.front.basket.objects.BaseBasket
        """
        return self.checkout_process.basket

    @property
    def storage(self):
        if not hasattr(self, "_storage"):
            self._storage = CheckoutPhaseStorage(request=self.request, phase_identifier=self.identifier)
        return self._storage

    def get_context_data(self, **kwargs):
        context = super(CheckoutPhaseViewMixin, self).get_context_data(**kwargs)
        context["current_phase_url"] = self.get_url()
        context["next_phase_url"] = (self.next_phase.get_url()
                                     if self.next_phase else None)
        context["previous_phase_url"] = (self.previous_phase.get_url()
                                         if self.previous_phase else None)
        context["phase_urls"] = {
            phase.identifier: phase.get_url()
            for phase in self.phases
        }

        return context


def _get_dummy_checkout_process(phase):
    phase_specs = ['{0.__module__}:{0.__name__}'.format(type(phase))]
    phase_kwargs = {
        key: getattr(phase, key)
        for key in ['request', 'args', 'kwargs'] if hasattr(phase, key)
    }
    checkout_process = CheckoutProcess(phase_specs, phase_kwargs)
    checkout_process._phases = [phase]
    checkout_process.horizontal_template = phase.horizontal_template
    return checkout_process
