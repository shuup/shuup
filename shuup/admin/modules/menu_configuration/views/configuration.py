from django.views.generic import FormView
from django.http import HttpResponse
from shuup.admin.modules.menu_configuration.form import ConfigurationForm


class MenuConfigurationFormView(FormView):
    template_name = "shuup/admin/menu_configuration/form.jinja"
    form_class = ConfigurationForm

    def get_form_kwargs(self):
        kwargs = super(MenuConfigurationFormView, self).get_form_kwargs()
        return kwargs