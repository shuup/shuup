import pytest
from unittest import TestCase

from shuup.core.excs import InvalidOrderStatusError
from shuup.core.models import DefaultOrderStatus, OrderStatus, OrderStatusManager
from shuup.testing import factories


@pytest.mark.django_db
class ChangeStatusTestCases(TestCase):
    def setUp(self):
        OrderStatusManager().ensure_default_statuses()
        product = factories.create_product("p", factories.get_default_shop(), factories.get_default_supplier())

        customer = factories.create_random_person()
        # Initial Order
        intial_status = OrderStatus.objects.filter(identifier=DefaultOrderStatus.INITIAL.value).first()
        self.order_initial = factories.create_random_order(customer=customer, products=[product])
        self.order_initial.change_status(intial_status)

        # Processing Order
        process_status = OrderStatus.objects.filter(identifier=DefaultOrderStatus.PROCESSING.value).first()
        self.order_processing = factories.create_random_order(customer=customer, products=[product])
        self.order_processing.change_status(process_status)

        # Complete Order
        complete_status = OrderStatus.objects.filter(identifier=DefaultOrderStatus.COMPLETE.value).first()
        self.order_complete = factories.create_random_order(customer=customer, products=[product])
        self.order_complete.change_status(complete_status)

        # Canceled Order
        canceled_status = OrderStatus.objects.filter(identifier=DefaultOrderStatus.CANCELED.value).first()
        self.order_canceled = factories.create_random_order(customer=customer, products=[product])
        self.order_canceled.change_status(canceled_status)

    def test_change_status_from_initial_to_canceled(self):
        next_status = OrderStatus.objects.filter(identifier=DefaultOrderStatus.CANCELED.value).first()
        self.order_initial.change_status(next_status=next_status)
        # self.assertEqual(self.order_initial.status.identifier, next_status.identifier)
        self.assertTrue(self.order_initial.status.identifier == next_status.identifier)

    def test_change_status_from_initial_to_in_progress(self):
        next_status = OrderStatus.objects.filter(identifier=DefaultOrderStatus.PROCESSING.value).first()
        self.order_initial.change_status(next_status=next_status)
        self.assertEqual(self.order_initial.status.identifier, next_status.identifier)

    def test_change_status_from_initial_to_complete(self):
        next_status = OrderStatus.objects.filter(identifier=DefaultOrderStatus.COMPLETE.value).first()
        self.order_initial.change_status(next_status=next_status)
        self.assertEqual(self.order_initial.status.identifier, next_status.identifier)

    def test_change_status_from_complete_to_other_status(self):
        next_status = OrderStatus.objects.filter(identifier=DefaultOrderStatus.INITIAL.value).first()
        with pytest.raises(InvalidOrderStatusError):
            self.order_complete.change_status(next_status=next_status)

    def test_change_status_from_canceled_to_other_status(self):
        next_status = OrderStatus.objects.filter(identifier=DefaultOrderStatus.INITIAL.value).first()
        with pytest.raises(InvalidOrderStatusError):
            self.order_canceled.change_status(next_status=next_status)
