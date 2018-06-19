# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from registration.forms import RegistrationForm

from shuup.core.models import CompanyContact, get_person_contact, PersonContact
from shuup.front.utils.companies import (
    company_registration_requires_approval, TaxNumberCleanMixin
)
from shuup.utils.djangoenv import has_installed
from shuup.utils.form_group import FormGroup
from shuup.utils.importing import cached_load


class CompanyForm(TaxNumberCleanMixin, forms.ModelForm):
    class Meta:
        model = CompanyContact
        fields = ['name', 'name_ext', 'tax_number', 'email', 'phone', 'www']
        help_texts = {
            'name': _("Name of the company"),
            'email': None, 'phone': None,
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(CompanyForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['tax_number'].required = True
        address_form = cached_load('SHUUP_ADDRESS_MODEL_FORM')()
        for field in self.fields:
            if field not in ('name', 'tax_number', 'www'):
                address_formfield = address_form.fields.get(field)
                if address_formfield:
                    self.fields[field].required = address_formfield.required
                else:
                    del self.fields[field]


class ContactPersonForm(forms.ModelForm):
    class Meta:
        model = PersonContact
        fields = ['first_name', 'last_name', 'email', 'phone']

    def __init__(self, **kwargs):
        super(ContactPersonForm, self).__init__(**kwargs)
        for (field_name, formfield) in self.fields.items():
            if field_name in ['first_name', 'last_name', 'email']:
                formfield.required = True
                formfield.help_text = None


class PersonRegistrationForm(RegistrationForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(PersonRegistrationForm, self).__init__(*args, **kwargs)

        if has_installed("shuup.gdpr"):
            from shuup.gdpr.models import GDPRSettings
            if GDPRSettings.get_for_shop(self.request.shop).enabled:
                from shuup.simple_cms.models import Page, PageType
                for page in Page.objects.visible(self.request.shop).filter(page_type=PageType.REVISIONED):
                    self.fields["accept_{}".format(page.id)] = forms.BooleanField(
                        label=_("I have read and accept the {}").format(page.title),
                        help_text=_("Read the <a href='{}' target='_blank'>{}</a>.").format(
                            reverse("shuup:cms_page", kwargs=dict(url=page.url)),
                            page.title
                        ),
                        error_messages=dict(required=_("You must accept to this to register."))
                    )

    def save(self, *args, **kwargs):
        user = super(PersonRegistrationForm, self).save(*args, **kwargs)
        get_person_contact(user).shops.add(self.request.shop)

        if has_installed("shuup.gdpr"):
            from shuup.gdpr.utils import create_user_consent_for_all_documents
            create_user_consent_for_all_documents(self.request.shop, user)

        return user


class CompanyAgreementForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.shop = kwargs.pop("shop")
        super(CompanyAgreementForm, self).__init__(*args, **kwargs)
        from shuup.simple_cms.models import Page, PageType
        for page in Page.objects.visible(self.shop).filter(page_type=PageType.REVISIONED):
            self.fields["accept_{}".format(page.id)] = forms.BooleanField(
                label=_("I have read and accept the {}").format(page.title),
                help_text=_("Read the <a href='{}' target='_blank'>{}</a>.").format(
                    reverse("shuup:cms_page", kwargs=dict(url=page.url)),
                    page.title
                ),
                error_messages=dict(required=_("You must accept this to register."))
            )


class CompanyRegistrationForm(FormGroup):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(CompanyRegistrationForm, self).__init__(*args, **kwargs)
        address_form_cls = cached_load('SHUUP_ADDRESS_MODEL_FORM')
        self.add_form_def('company', CompanyForm, kwargs={"request": self.request})
        self.add_form_def('billing', address_form_cls)
        self.add_form_def('contact_person', ContactPersonForm)
        self.add_form_def('user_account', UserCreationForm)

        if has_installed("shuup.gdpr"):
            from shuup.gdpr.models import GDPRSettings
            if GDPRSettings.get_for_shop(self.request.shop).enabled:
                self.add_form_def('agreement', CompanyAgreementForm, kwargs=dict(shop=self.request.shop))

    def instantiate_forms(self):
        super(CompanyRegistrationForm, self).instantiate_forms()
        company_form = self.forms['company']
        billing_form = self.forms['billing']
        for field in list(billing_form.fields):
            billing_form.fields[field].help_text = None
            if field in company_form.fields:
                del billing_form.fields[field]

    def save(self, commit=True):
        company = self.forms['company'].save(commit=False)
        billing_address = self.forms['billing'].save(commit=False)
        person = self.forms['contact_person'].save(commit=False)
        user = self.forms['user_account'].save(commit=False)

        company.default_billing_address = billing_address
        company.default_shipping_address = billing_address

        for field in ['name', 'name_ext', 'email', 'phone']:
            setattr(billing_address, field, getattr(company, field))

        person.user = user

        user.first_name = person.first_name
        user.last_name = person.last_name
        user.email = person.email

        # If company registration requires approval,
        # company and person contacts will be created as inactive
        if company_registration_requires_approval(self.request.shop):
            company.is_active = False
            person.is_active = False

        if commit:
            user.save()
            person.user = user
            person.save()
            person.shops.add(self.request.shop)
            billing_address.save()
            company.default_billing_address = billing_address
            company.default_shipping_address = billing_address
            company.save()
            company.shops.add(self.request.shop)
            company.members.add(person)

        if has_installed("shuup.gdpr"):
            from shuup.gdpr.utils import create_user_consent_for_all_documents
            create_user_consent_for_all_documents(self.request.shop, user)

        return user
