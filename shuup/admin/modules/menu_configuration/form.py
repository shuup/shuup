from django import forms

class ConfigurationForm(forms.Form):
    name = forms.CharField()