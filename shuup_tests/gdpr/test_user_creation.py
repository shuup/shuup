import random
import pytest

from django.core.urlresolvers import reverse

from shuup.core import cache
from shuup.core.models import Order, Product, get_person_contact, PersonContact
from shuup.front.signals import checkout_complete
from shuup.gdpr.models import GDPRSettings
from shuup.testing.factories import (
    create_default_order_statuses, get_address, get_default_shop,
    get_default_supplier,
)
from shuup.testing.mock_population import populate_if_required
from shuup.testing.soup_utils import extract_form_fields
from shuup_tests.front.utils import checkout_complete_signal
from shuup_tests.utils import SmartClient
from shuup_tests.utils.fixtures import (
    regular_user, REGULAR_USER_PASSWORD, REGULAR_USER_USERNAME
)


def fill_address_inputs(soup):
    inputs = {}
    test_address = get_address()
    for key, value in extract_form_fields(soup.find('form', id='addresses')).items():
        if not value:
            if key in ("order-tax_number", "order-company_name"):
                continue
            if key.startswith("shipping-") or key.startswith("billing-"):
                bit = key.split("-")[1]
                value = getattr(test_address, bit, None)
            if not value and "email" in key:
                value = "test%d@example.shuup.com" % random.random()
            if not value:
                value = "test"
        inputs[key] = value
        inputs = dict((k, v) for (k, v) in inputs.items() if not k.startswith("company-"))

    return inputs

def initialize_client_and_parameters(regular_user):
    client = SmartClient()
    shop = get_default_shop()
    contact = get_person_contact(regular_user)

    client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
    return client, shop, contact

def _populate_client_basket(client):
    product_ids = []
    index = client.soup("/")
    product_links = index.find_all("a", rel="product-detail")
    assert product_links
    for i in range(3):
        product_detail_path = product_links[i]["href"]
        assert product_detail_path
        product_detail_soup = client.soup(product_detail_path)
        inputs = extract_form_fields(product_detail_soup)
        basket_path = reverse("shuup:basket")
        basket_data = {
            "command": "add",
            "product_id": inputs["product_id"],
            "quantity": 1,
            "supplier": get_default_supplier().pk,
        }
        add_to_basket_resp = client.post(basket_path, data=basket_data)
        assert add_to_basket_resp.status_code < 400
        product_ids.append(inputs["product_id"])
    basket_soup = client.soup(basket_path)
    assert b'no such element' not in basket_soup.renderContents(), 'All product details are not rendered correctly'
    return product_ids

@pytest.mark.parametrize("gdpr_enabled, create_contact", [
    (True, True),
    (False, True),
    (True, False),
    (False, False),
])
def test_user_creation_in_order_flow(regular_user, gdpr_enabled, create_contact):
    cache.clear()
    create_default_order_statuses()
    n_orders_pre = Order.objects.count()
    populate_if_required()
    if create_contact:
        c, shop, contact = initialize_client_and_parameters(regular_user)
    else:
        c = SmartClient()
        shop = get_default_shop()
    product_ids = _populate_client_basket(c)

    if gdpr_enabled:
        gdpr_settings = GDPRSettings.get_for_shop(shop)
        gdpr_settings.enabled = True
        gdpr_settings.save()
    else:
        gdpr_settings = GDPRSettings.get_for_shop(shop)
        gdpr_settings.enabled = False
        gdpr_settings.save()
    addresses_path = reverse("shuup:checkout", kwargs={"phase": "addresses"})
    addresses_soup = c.soup(addresses_path)
    inputs = fill_address_inputs(addresses_soup)
    response = c.post(addresses_path, data=inputs)
    assert response.status_code == 302  # Should redirect forth

    # Make sure the address is initialized from storage
    # Go back to addresses right before back to methods
    c.soup(addresses_path)

    methods_path = reverse("shuup:checkout", kwargs={"phase": "methods"})
    methods_soup = c.soup(methods_path)
    assert c.post(methods_path, data=extract_form_fields(methods_soup)).status_code == 302  # Should redirect forth

    checkout_complete.connect(checkout_complete_signal, dispatch_uid="checkout_complete_signal")

    confirm_path = reverse("shuup:checkout", kwargs={"phase": "confirm"})
    confirm_soup = c.soup(confirm_path)
    Product.objects.get(pk=product_ids[0]).soft_delete()
    assert c.post(confirm_path, data=extract_form_fields(confirm_soup)).status_code == 200  # user needs to reconfirm
    data = extract_form_fields(confirm_soup)
    data['product_ids'] = ','.join(product_ids[1:])
    assert c.post(confirm_path, data=data).status_code == 302  # Should redirect forth

    n_orders_post = Order.objects.count()
    assert n_orders_post > n_orders_pre, "order was created"

    order = Order.objects.first()
    expected_ip = "127.0.0.2"
    assert order.ip_address == expected_ip
    if create_contact:
        assert order.orderer == contact
    elif gdpr_enabled:
        assert type(order.orderer) == PersonContact

    checkout_complete.disconnect(dispatch_uid="checkout_complete_signal")
