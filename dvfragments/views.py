from typing import List, Tuple

from django.template.base import Node
from django.template.context import make_context
from django.template.response import TemplateResponse


URL_FRAGMENT_QUERY_KEY = 'fragment'


class ConcatenatedTemplatesResponse(TemplateResponse):
    def __init__(self, names_nodes: List[Tuple[str, Node]], **kwargs):
        kwargs['template'] = None
        super().__init__(**kwargs)
        self.names_nodes = names_nodes

    @property
    def rendered_content(self):
        if len(self.names_nodes) == 0:
            return ''
        context_data = self.resolve_context(self.context_data)
        # this is normally done by Template.render(), but we don't have a template and are rendering
        # directly from nodes so have to do it ourselves.
        engine = self.names_nodes[0][1].origin.loader.engine
        context = make_context(context_data, self._request, autoescape=engine.autoescape)
        contents = []
        for fragment_id, node in self.names_nodes:
            rendered = node.render(context)
            contents.append(rendered)

        return '\n'.join(contents)


class FragmentableTemplateViewMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['_dvviewclass'] = type(self)
        return context

    def render_to_response(self, context, **response_kwargs):
        if not hasattr(type(self), 'fragment_nodes_by_name'):
            type(self).fragment_nodes_by_name = {}

        # Cribbing from django.views.generic.base.TemplateResponseMixin
        response_kwargs.setdefault('content_type', self.content_type)
        fragments = self.request.GET.getlist(URL_FRAGMENT_QUERY_KEY)
        if not fragments:
            return super().render_to_response(context, **response_kwargs)

        fragments = list(set(fragments))

        if any(f not in self.fragment_nodes_by_name for f in fragments):
            super().render_to_response(context, **response_kwargs).render()

        return ConcatenatedTemplatesResponse(
            [(f, self.fragment_nodes_by_name[f]) for f in fragments],
            request=self.request,
            context=context,
            using=self.template_engine,
            **response_kwargs
        )
