import six
from django import forms
from shuup.configuration import set, get
from shuup.admin.module_registry import get_modules


class ConfigurationForm(forms.Form):
    name = forms.CharField()

    def __init__(self, **kwargs):
        # self.shop = kwargs.pop("shop")
        modules = list(get_modules())
        super(ConfigurationForm, self).__init__(**kwargs)
        # for module in modules:
        #     print(module.name)
        # for form_field, conf_key in six.iteritems(modules):
        #     self.initial[form_field] = configuration.get(self.shop, conf_key)