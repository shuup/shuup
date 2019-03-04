from django.views.generic import FormView
from django.http import HttpResponse
from shuup.admin.modules.menu_configuration.form import ConfigurationForm


class MenuConfigurationFormView(FormView):
    template_name = "shuup/admin/menu_configuration/form.jinja"
    form_class = ConfigurationForm

    def get_form_kwargs(self):
        # TODO: deprecate
        kwargs = super(MenuConfigurationFormView, self).get_form_kwargs()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(MenuConfigurationFormView, self).get_context_data(**kwargs)
        return context

    