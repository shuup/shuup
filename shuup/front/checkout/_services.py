# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import abc

import six

from shuup.apps.provides import get_provide_objects
from shuup.core.models import ServiceProvider

from ._view_mixin import CheckoutPhaseViewMixin


class ServiceCheckoutPhaseProvider(six.with_metaclass(abc.ABCMeta)):
    """
    Interface for providing checkout phase for a service.

    Items specified in ``front_service_checkout_phase_provider`` provide
    category should implement this interface.
    """

    @abc.abstractmethod
    def get_checkout_phase(self, checkout_process, service):
        """
        Get checkout phase for given service.

        If this provider is for another service, then the return value
        will be None.

        :type checkout_process: shuup.front.checkout.CheckoutProcess
        :type service: shuup.core.models.Service
        :rtype: shuup.front.checkout.CheckoutPhaseViewMixin|None
        """
        pass


class BasicServiceCheckoutPhaseProvider(ServiceCheckoutPhaseProvider):
    """
    Helper for implementing basic ServiceCheckoutPhaseProvider.

    This helper should be useful for most cases, where one only has to
    provide a checkout phase for certain service provider type just by
    initializing some predefined class.
    """
    phase_class = None  # override in subclass
    service_provider_class = None   # override in subclass

    def get_checkout_phase(self, checkout_process, service):
        """
        Get checkout phase for given service.

        :type checkout_process: shuup.front.checkout.CheckoutProcess
        :type service: shuup.core.models.Service
        :rtype: shuup.front.checkout.CheckoutPhaseViewMixin|None
        """
        assert issubclass(self.phase_class, CheckoutPhaseViewMixin)
        assert issubclass(self.service_provider_class, ServiceProvider)
        if isinstance(service.provider, self.service_provider_class):
            return checkout_process.instantiate_phase_class(
                self.phase_class, service=service)
        return None


def get_checkout_phases_for_service(checkout_process, service):
    """
    Get checkout phases for given service.

    :type checkout_process: shuup.front.checkout.CheckoutProcess
    :type service: shuup.core.models.Service
    :rtype: Iterable[shuup.front.checkout.CheckoutPhaseViewMixin]
    """
    classes = get_provide_objects("front_service_checkout_phase_provider")
    for provider_cls in classes:
        provider = provider_cls()
        assert isinstance(provider, ServiceCheckoutPhaseProvider)
        phase = provider.get_checkout_phase(checkout_process, service)
        if phase:
            assert isinstance(phase, CheckoutPhaseViewMixin)
            yield phase
