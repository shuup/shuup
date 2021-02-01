# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from shuup.admin.modules.contacts.forms import GroupMassEditForm, MassEditForm
from shuup.admin.utils.views import MassEditMixin
from shuup.core.models import Contact
from shuup.utils.django_compat import reverse


class ContactMassEditView(MassEditMixin, FormView):
    title = _("Mass Edit: Contacts")
    form_class = MassEditForm

    def form_valid(self, form):
        query = Q(id__in=self.ids)
        if isinstance(self.ids, six.string_types) and self.ids == "all":
            query = Q()
        for contact in Contact.objects.filter(query):
            for k, v in six.iteritems(form.cleaned_data):
                if not v:
                    continue
                if hasattr(contact, k):
                    setattr(contact, k, v)
            contact.save()

        messages.success(self.request, _("Contacts were changed."))
        self.request.session["mass_action_ids"] = []
        return HttpResponseRedirect(reverse("shuup_admin:contact.list"))


class ContactGroupMassEditView(MassEditMixin, FormView):
    title = _("Mass Edit: Contact Groups")
    form_class = GroupMassEditForm

    def form_valid(self, form):
        ids = self.ids
        if isinstance(self.ids, six.string_types) and self.ids == "all":
            ids = set(Contact.objects.all().values_list("id", flat=True))
        groups = form.cleaned_data.get("contact_group", [])
        for group in groups:
            group.members.add(*ids)

        messages.success(self.request, _("Contacts Groups were changed."))
        self.request.session["mass_action_ids"] = []
        return HttpResponseRedirect(reverse("shuup_admin:contact.list"))
