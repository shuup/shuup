# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from collections import OrderedDict
from django.core.exceptions import ImproperlyConfigured
from django.http.response import Http404
from django.utils.html import escape

from shuup.front.basket import get_basket
from shuup.utils.django_compat import reverse
from shuup.utils.importing import load


class CheckoutProcess(object):
    horizontal_template = True

    def __init__(self, phase_specs, phase_kwargs, view=None):
        """
        Initialize this checkout process.

        :type phase_specs: list[str]
        :type phase_kwargs: dict
        :type view: shuup.front.checkout.BaseCheckoutView|None
        """
        self.phase_specs = phase_specs
        self.phase_kwargs = phase_kwargs
        self.view = view
        self.request = self.phase_kwargs.get("request")

    @property
    def phases(self):
        """
        :rtype: Iterable[CheckoutPhaseViewMixin]
        """
        if not getattr(self, "_phases", None):
            self._phases = self._load_phases()
        return self._phases

    def instantiate_phase_class(self, phase_class, **extra_kwargs):
        if not phase_class.identifier:  # pragma: no cover
            raise ImproperlyConfigured("Error! Phase `%r` has no identifier." % phase_class)
        kwargs = {}
        kwargs.update(self.phase_kwargs)
        kwargs.update(extra_kwargs)
        phase = phase_class(checkout_process=self, horizontal_template=self.horizontal_template, **kwargs)
        return phase

    def _load_phases(self):
        phases = OrderedDict()

        for phase_spec in self.phase_specs:
            phase_class = load(phase_spec)
            phase = self.instantiate_phase_class(phase_class)
            phases[phase_class.identifier] = phase

            # check whether the phase spawns new phases,
            # if so, then let's spawn then and add the phases
            for spawned_phase in phase.spawn_phases(self):
                phases[spawned_phase.identifier] = spawned_phase

        return list(phases.values())

    def get_current_phase(self, requested_phase_identifier):
        found = False
        for phase in self.phases:
            if phase.is_valid():
                phase.process()
            if found or not requested_phase_identifier or requested_phase_identifier == phase.identifier:
                found = True  # We're at or past the requested phase
                if not phase.should_skip():
                    return phase
            if not phase.should_skip() and not phase.is_valid():  # A past phase is not valid, that's the current one
                return phase
        raise Http404("Error! Phase with identifier `%s` not found." % escape(requested_phase_identifier))

    def _get_next_phase(self, phases, current_phase, target_phase):
        found = False
        for phase in phases:
            if phase.identifier == current_phase.identifier:
                # Found the current one, so any valid phase from here on out is the next one
                found = True
                continue

            if found and current_phase.identifier != target_phase.identifier:
                return phase

            if found and not phase.should_skip():
                # Yep, that's the one
                return phase

    def get_next_phase(self, current_phase, target_phase):
        return self._get_next_phase(self.phases, current_phase, target_phase)

    def get_previous_phase(self, current_phase, target_phase):
        return self._get_next_phase(reversed(self.phases), current_phase, target_phase)

    def prepare_current_phase(self, phase_identifier):
        current_phase = self.get_current_phase(phase_identifier)
        self.add_phase_attributes(current_phase)
        self.current_phase = current_phase
        return current_phase

    def add_phase_attributes(self, target_phase, current_phase=None):
        """
        Add phase instance attributes (previous, next, etc) to the given target phase,
        using the optional `current_phase` as the current phase for previous and next.

        This is exposed as a public API for the benefit of phases that need to do sub-phase
        initialization and dispatching, such as method phases.
        """
        current_phase = current_phase or target_phase
        target_phase.previous_phase = self.get_previous_phase(current_phase, target_phase)
        target_phase.next_phase = self.get_next_phase(current_phase, target_phase)
        target_phase.phases = self.phases
        if current_phase in self.phases:
            current_phase_index = self.phases.index(current_phase)
            # Set up attributes that are handy for the phase bar in the templates.
            for i, phase in enumerate(self.phases):
                setattr(phase, "is_past", i > current_phase_index)
                setattr(phase, "is_current", phase == current_phase)
                setattr(phase, "is_future", i < current_phase_index)
                setattr(phase, "is_previous", phase == target_phase.previous_phase)
                setattr(phase, "is_next", phase == target_phase.next_phase)
        return target_phase

    def reset(self):
        for phase in self.phases:
            phase.reset()

    def complete(self):
        """
        To be called from a phase (`self.checkout_process.complete()`) when the checkout process is complete.
        """
        self.reset()

    def get_phase_url(self, phase):
        # The self.view is optional for backward compatibility
        if not self.view:
            url_kwargs = {"phase": phase.identifier}
            return reverse("shuup:checkout", kwargs=url_kwargs)
        return self.view.get_phase_url(phase)

    @property
    def basket(self):
        """
        The basket used in this checkout process.

        :rtype: shuup.front.basket.objects.BaseBasket
        """
        return get_basket(self.request)


class VerticalCheckoutProcess(CheckoutProcess):
    horizontal_template = False
