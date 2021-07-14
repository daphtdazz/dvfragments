from django import template
from django.template.exceptions import TemplateSyntaxError
from django.template.loader_tags import Node

from ..utils import add_fragment_id


register = template.Library()


class FragmentNode(Node):
    def __init__(self, fragment_id, nodelist):
        super().__init__()
        self.fragment_id = fragment_id
        self.nodelist = nodelist

    def render(self, context):
        context['_dvviewclass'].fragment_nodes_by_name[self.fragment_id] = self
        rendered = ''.join(node.render(context) for node in self.nodelist)
        rendered2 = add_fragment_id(rendered, self.fragment_id)
        return rendered2


@register.tag(name='fragment')
def do_fragment(parser, token):
    """
    Same arguments as for ``{% include %}`` except instead of passing a template path you pass
    the name of the fragment. Otherwise behaviour basically the same as `include`.

    Example::

        {% include fragment-name %}
        {% include fragment-name with bar="BAZZ!" baz="BING!" %}
    """
    # Cribbed heavily from django.template.loader_tags.do_include
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError(
            "'fragment' tag takes at least one argument: the name of the fragment to be rendered."
        )

    if len(bits) > 2:
        raise TemplateSyntaxError(
            "The 'fragment' tag only takes one argument, the name. Was passed {', '.join(bits[1:])}"
        )

    fragment_name = bits[1]
    if not fragment_name:
        raise TemplateSyntaxError('Must provide a fragment name')

    nodelist = parser.parse(('endfragment',))
    parser.delete_first_token()

    return FragmentNode(bits[1], nodelist)
