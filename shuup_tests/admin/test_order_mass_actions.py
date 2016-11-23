import json

import pytest
from shuup.admin.modules.orders.mass_actions import CancelOrderAction
from shuup.admin.modules.orders.views import OrderListView
from shuup.core.models import Order
from shuup.core.models import OrderStatusRole
from shuup.testing.factories import get_default_supplier, get_default_shop, create_random_order, create_product, \
    create_random_person
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import printable_gibberish

try:
    import weasyprint
except ImportError:
    weasyprint = None

@pytest.mark.django_db
def test_mass_edit_orders(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    contact1 = create_random_person()
    product1 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="50")
    product2 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="501")

    order = create_random_order(customer=contact1,
                                products=[product1, product2],
                                completion_probability=0)

    assert order.status.role != OrderStatusRole.CANCELED
    payload = {
        "action": CancelOrderAction().identifier,
        "values": [order.pk]
    }
    request = apply_request_middleware(rf.post(
        "/",
        user=admin_user,
    ))
    request._body = json.dumps(payload).encode("UTF-8")
    view = OrderListView.as_view()
    response = view(request=request)
    assert response.status_code == 200
    for order in Order.objects.all():
        assert order.status.role == OrderStatusRole.CANCELED
