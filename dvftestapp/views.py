from django.views.generic.base import TemplateView

from dvfragments.views import FragmentableTemplateViewMixin

class View1(FragmentableTemplateViewMixin, TemplateView):
    template_name = 'dvftestapp/view1.html'
    fragments = {}

    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs)
        c['condition'] = self.request.GET.get('condition')
        return c
