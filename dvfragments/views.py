class FragmentableViewMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['_dvfragments'] = self.fragments
        return context
