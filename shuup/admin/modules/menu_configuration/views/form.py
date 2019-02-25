from django.views.generic import FormView
from django.http import HttpResponse

class MenuConfigurationFormView(FormView):
    def get(self, request):
        return HttpResponse('Menu Configuration')
