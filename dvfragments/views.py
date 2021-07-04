import re
from typing import Iterable, Tuple

from django.conf import settings
from django.template.response import TemplateResponse


URL_FRAGMENT_QUERY_KEY = 'fragment'

FIRST_ELEMENT_RE = re.compile(r'^(\s*<\s*\w+\s)')


class ConcatenatedTemplatesResponse(TemplateResponse):
    """This is the same as TemplateResponse only instead of passing a list of strings for the
    template arg of the constructor, you have to pass a List[List[str]] as we may need to render
    multiple fragment templates."""
    def __init__(self, templates_options: Iterable[Tuple[str, Iterable[str]]], **kwargs):
        kwargs['template'] = None
        super().__init__(**kwargs)
        self.templates_options = templates_options

    @property
    def rendered_content(self):
        context = self.resolve_context(self.context_data)
        contents = []
        for fragment_name, template_names in self.templates_options:
            template = self.resolve_template(template_names)
            rendered = template.render(context, self._request)

            rendered2 = FIRST_ELEMENT_RE.sub(rf'\1x-dvfragment-id={fragment_name} ', rendered)
            contents.append(rendered2)

        return '\n'.join(contents)


class FragmentableTemplateViewMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['_dvfragments'] = self.fragments
        return context

    def render_to_response(self, context, **response_kwargs):
        # Cribbing from django.views.generic.base.TemplateResponseMixin
        response_kwargs.setdefault('content_type', self.content_type)
        fragments = self.request.GET.getlist(URL_FRAGMENT_QUERY_KEY)
        if not fragments:
            return super().render_to_response(context, **response_kwargs)

        fragments = list(set(fragments))
        return ConcatenatedTemplatesResponse(
            [(frag, [self.fragments[frag]]) for frag in fragments],
            request=self.request,
            context=context,
            using=self.template_engine,
            **response_kwargs
        )
