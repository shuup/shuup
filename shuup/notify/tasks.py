# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from six.moves.urllib.parse import urljoin

from shuup.core.models import Shop
from shuup.notify.notify_events import PasswordReset


def send_user_reset_password_email(user_id: int, shop_id: int, reset_domain_url: str, reset_url_name: str):
    shop = Shop.objects.get(pk=shop_id)
    user = get_user_model().objects.get(pk=user_id)
    uid = urlsafe_base64_encode(force_bytes(user_id))
    token = default_token_generator.make_token(user)
    recovery_url = urljoin(reset_domain_url, reverse(reset_url_name, kwargs=dict(uidb64=uid, token=token)))
    context = {
        "site_name": shop.public_name,
        "uid": uid,
        "user_to_recover": user,
        "token": token,
        "customer_email": user.email,
        "recovery_url": recovery_url,
    }
    PasswordReset(**context).run(shop=shop)
