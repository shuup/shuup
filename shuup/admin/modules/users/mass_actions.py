# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import PicotableMassAction
from shuup.core.shop_provider import get_shop
from shuup.core.utils.users import send_user_reset_password_email


class UserMassActionProvider(object):
    @classmethod
    def get_mass_actions_for_view(cls, view):
        return ["shuup.admin.modules.users.mass_actions.ResetPasswordAction"]


class ResetPasswordAction(PicotableMassAction):
    label = _("Send Reset Password Email")
    identifier = "mass_action_user_reset_password_email"

    def process(self, request, ids):
        shop = get_shop(request)
        reset_domain_url = request.build_absolute_uri("/")

        if isinstance(ids, str) and ids == "all":
            query = Q()
        else:
            query = Q(pk__in=ids)

        for user in get_user_model().objects.filter(query):
            # if user is staff, then use the admin url and templates
            if user.is_staff or user.is_superuser:
                reset_url_name = "shuup_admin:recover_password"
                subject_template_name = "shuup/admin/auth/recover_password_mail_subject.jinja"
                email_template_name = "shuup/admin/auth/recover_password_mail_content.jinja"
            else:
                reset_url_name = "shuup:recover_password_confirm"
                subject_template_name = "shuup/user/recover_password_mail_subject.jinja"
                email_template_name = "shuup/user/recover_password_mail_content.jinja"

            send_user_reset_password_email(
                user=user,
                shop=shop,
                reset_domain_url=reset_domain_url,
                reset_url_name=reset_url_name,
                token_generator=default_token_generator,
                subject_template_name=subject_template_name,
                email_template_name=email_template_name,
            )
