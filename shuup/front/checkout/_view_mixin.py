# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import reverse

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

    def get_success_url(self):
        if self.next_phase:
            return reverse("shuup:checkout", kwargs={"phase": self.next_phase.identifier})

    @property
    def storage(self):
        if not hasattr(self, "_storage"):
            self._storage = CheckoutPhaseStorage(request=self.request, phase_identifier=self.identifier)
        return self._storage
