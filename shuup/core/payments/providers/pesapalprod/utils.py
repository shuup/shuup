import pesapal
from django.conf import settings
from django.urls import reverse

from shuup.core.payments.providers.pesapalprod.models import PesapalPayment

pesapal.consumer_key = settings.PESAPAL_CONSUMER_KEY
pesapal.consumer_secret = settings.PESAPAL_CONSUMER_SECRET
pesapal.testing = settings.PESAPAL_TESTING


def transform_basket_line_to_line_item(basket_line):
    return {
        'uniqueid': basket_line.line_id,
        'particulars': basket_line.product.name,
        'quantity': str(basket_line.quantity),
        'unitcost': f"{basket_line.taxful_base_unit_price.value:.2f}",
        'subtotal': f"{basket_line.taxful_price.value:.2f}"
    }


def get_callback_url(request):
    domain = request.get_host()
    protocol = "https" if request.is_secure() else "http"
    path = reverse('shuup:checkout', args=['methods'])
    return f"{protocol}://{domain}{path}"


def get_pesapal_payment_url(request, amount, reference, description=None, phone_number=None, lines=[]):
    lines = list(map(transform_basket_line_to_line_item, lines))
    if not description:
        if lines:
            products = [line['particulars'] for line in lines]
            description = ",".join(products)
        else:
            description = f"Basket {reference}"
    phone_number = phone_number or settings.DEFAULT_PESAPAL_PHONE_NUMBER

    request_data = {
        'Amount': f"{amount:.2f}",
        'Description': description,
        'Type': 'MERCHANT',
        'Reference': reference,
        'LineItems': lines,
        'PhoneNumber': phone_number
    }
    # build url to redirect user to confirm payment
    post_params = dict(oauth_callback=get_callback_url(request))
    url = pesapal.postDirectOrder(post_params, request_data)
    pp, _ = PesapalPayment.objects.get_or_create(merchant_reference=reference)
    pp.amount = amount
    pp.payment_url = url
    pp.save()
    return url
