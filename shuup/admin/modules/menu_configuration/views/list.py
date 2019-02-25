from django.views.generic import View
from django.http import HttpResponse


class MenuConfigurationListView(View):
    def get(self, request):
        return HttpResponse('Menu Configuration')
