# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_user_model
from django.db.models.loading import get_model
from django.db.transaction import atomic
from django.forms import BaseModelForm
from django.utils.translation import ugettext_lazy as _

from shoop.admin.form_part import (
    FormPart, FormPartsViewMixin, SaveFormPartsMixin, TemplatedFormDef
)
from shoop.admin.toolbar import get_default_edit_toolbar
from shoop.admin.utils.urls import get_model_url
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import (
    CompanyContact, Contact, ContactGroup, ImmutableAddress, MutableAddress,
    PersonContact
)
from shoop.utils.excs import Problem
from shoop.utils.form_group import FormDef


class ContactBaseForm(BaseModelForm):
    """
    This form is notoriously confusing in that it works in several different modes
    depending on what the instance being passed in is.

    If the instance is an unsaved object, the form will show fields for the common
    superclass Contact as well as a type selection field.
    When saving the object, a _new_ instance is created, as its class will have been
    specialized into the actual concrete polymorphic type. (I said this is confusing.)

    If the instance is a saved object, its type is checked and only the related
    fields are shown and none of that specialization stuff occurs.

    """

    FIELDS_BY_MODEL_NAME = {
        "Contact": (
            "is_active", "language", "marketing_permission", "phone", "www",
            "timezone", "prefix", "suffix", "name_ext", "email", "tax_group",
            "merchant_notes"
        ),
        "PersonContact": (
            "gender", "birth_date", "first_name", "last_name"
        ),
        "CompanyContact": (
            "name", "tax_number",
        )
    }

    def __init__(self, bind_user=None, *args, **kwargs):
        class Meta:  # faux ModelForm Meta
            model = Contact
            fields = ()
            exclude = ()

        self.base_fields = {}
        self._meta = Meta
        super(ContactBaseForm, self).__init__(*args, **kwargs)
        self.contact_class = None
        self.bind_user = bind_user

        if self.bind_user:
            self.contact_class = PersonContact
            self.initial.setdefault("name", self.bind_user.get_full_name())
        if self.instance.pk:
            self.contact_class = self.instance.__class__

        self.generate_fields()

    def generate_fields(self):
        self.fields["type"] = forms.ChoiceField(choices=[
            ("PersonContact", _("Person")),
            ("CompanyContact", _("Company"))
        ], label=_("Type"))
        self.fields["groups"] = forms.ModelMultipleChoiceField(
            queryset=ContactGroup.objects.all(),
            initial=(self.instance.groups.all() if self.instance.pk else ()),
            required=False,
            widget=forms.CheckboxSelectMultiple(),
            label=_("Contact Groups")
        )
        self.fields_by_model = {}

        classes = (Contact, PersonContact, CompanyContact)
        if self.contact_class:
            classes = (self.contact_class, Contact,)
            self._meta.model = classes[0]

        for model_cls in classes:
            model_name = str(model_cls.__name__)
            model_fields = forms.fields_for_model(model_cls, fields=self.FIELDS_BY_MODEL_NAME[model_name])
            self.fields_by_model[model_name] = model_fields
            self.fields.update(model_fields.items())

        if self.contact_class:
            self.fields.pop("type")  # Can't change that.

        if not self.instance.pk:
            self.fields.pop("is_active")

    def set_model_from_cleaned_data(self):
        if "type" in self.fields:
            contact_type = self.cleaned_data["type"]
        else:
            contact_type = str(self._meta.model.__name__)

        self._meta.fields = set(self.fields_by_model["Contact"]) | set(self.fields_by_model[contact_type])
        self._meta.model = get_model("shoop", contact_type)
        if not self.instance.pk:  # For new objects, "materialize" the abstract superclass.
            self.instance = self._meta.model()
        assert issubclass(self._meta.model, Contact)

    def _clean_fields(self):
        super(ContactBaseForm, self)._clean_fields()
        self.set_model_from_cleaned_data()

    def save(self, commit=True):
        obj = super(ContactBaseForm, self).save(commit)
        if self.bind_user and not getattr(obj, "user", None):  # Allow binding only once
            obj.user = self.bind_user
            obj.save()

        obj.groups = self.cleaned_data["groups"]
        return obj


class ContactBaseFormPart(FormPart):
    priority = -1000  # Show this first, no matter what

    def get_form_defs(self):
        bind_user_id = self.request.REQUEST.get("user_id")
        if bind_user_id:
            bind_user = get_user_model().objects.get(pk=bind_user_id)
            if PersonContact.objects.filter(user=bind_user).exists():
                raise Problem(_("User %(bind_user)s already has a contact", bind_user=bind_user))
        else:
            bind_user = None
        yield TemplatedFormDef(
            "base",
            ContactBaseForm,
            template_name="shoop/admin/contacts/_edit_base_form.jinja",
            required=True,
            kwargs={"instance": self.object, "bind_user": bind_user}
        )

    def form_valid(self, form):
        self.object = form["base"].save()
        return self.object  # Identity may have changed (not the original object we put in)


class AddressForm(forms.ModelForm):
    class Meta:
        model = MutableAddress
        fields = (
            "prefix", "name", "suffix", "name_ext",
            "phone", "email",
            "street", "street2", "street3",
            "postal_code", "city",
            "region_code", "region",
            "country"
        )


class ContactAddressesFormPart(FormPart):
    priority = -900

    def get_form_defs(self):
        initial = {}  # TODO: should we do this? model_to_dict(self.object, AddressForm._meta.fields)
        yield FormDef(
            name="shipping_address", form_class=AddressForm,
            required=False, kwargs={"instance": self.object.default_shipping_address, "initial": initial}
        )
        yield FormDef(
            name="billing_address", form_class=AddressForm,
            required=False, kwargs={"instance": self.object.default_billing_address, "initial": initial}
        )
        # Using a pseudo formdef to group the two actual formdefs...
        yield TemplatedFormDef(
            name="addresses", form_class=forms.Form,
            required=False, template_name="shoop/admin/contacts/_edit_addresses_form.jinja"
        )

    def form_valid(self, form):
        for obj_key, form_name in [
            ("default_shipping_address", "shipping_address"),
            ("default_billing_address", "billing_address"),
        ]:
            addr_form = form[form_name]
            if addr_form.changed_data:
                if addr_form.instance.pk and isinstance(addr_form.instance, ImmutableAddress):
                    addr_form.instance.pk = None  # Force resave
                addr = addr_form.save()
                setattr(self.object, obj_key, addr)
                self.object.save()


class ContactEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = Contact
    template_name = "shoop/admin/contacts/edit.jinja"
    context_object_name = "contact"
    base_form_part_classes = [ContactBaseFormPart, ContactAddressesFormPart]
    form_part_class_provide_key = "admin_contact_form_part"

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)

    def get_toolbar(self):
        toolbar = get_default_edit_toolbar(
            self,
            self.get_save_form_id(),
            discard_url=(get_model_url(self.object) if self.object.pk else None)
        )
        # TODO: Add extensibility
        return toolbar
