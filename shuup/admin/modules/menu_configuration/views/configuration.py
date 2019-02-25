from django.views.generic import FormView
from django.http import HttpResponse
from shuup.admin.modules.menu_configuration.form import ConfigurationForm

class MenuConfigurationFormView(FormView):
    template_name = "shuup/admin/menu_configuration/form.jinja"
    form_class = ConfigurationForm

    # def get(self, request):
    #     return HttpResponse('Menu Configuration')
