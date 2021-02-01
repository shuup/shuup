# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import PicotableRedirectMassAction
from shuup.utils.django_compat import reverse


class EditContactsAction(PicotableRedirectMassAction):
    label = _("Edit Contacts")
    identifier = "mass_action_edit_contact"
    redirect_url = reverse("shuup_admin:contact.mass_edit")


class EditContactGroupsAction(PicotableRedirectMassAction):
    label = _("Set Contact Groups")
    identifier = "mass_action_edit_contact_group"
    redirect_url = reverse("shuup_admin:contact.mass_edit_group")
