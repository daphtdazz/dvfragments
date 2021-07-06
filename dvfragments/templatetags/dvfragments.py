from django import template
from django.template.base import FilterExpression, Parser
from django.template.loader_tags import IncludeNode

from ..utils import add_fragment_id


register = template.Library()


class FragmentNode(IncludeNode):
    def __init__(self, fragment_id, *, extra_context, isolated_context):
        self.fragment_id = fragment_id

        # template name is deferred
        super().__init__(None, extra_context=extra_context, isolated_context=isolated_context)

    def render(self, context):
        token = context['_dvfragments'][self.fragment_id]
        self.template = FilterExpression(f'"{token}"', Parser(''))
        rendered = super().render(context)
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
            "%r tag takes at least one argument: the name of the fragment to "
            "be rendered." % bits[0]
        )
    options = {}
    remaining_bits = bits[2:]
    while remaining_bits:
        option = remaining_bits.pop(0)
        if option in options:
            raise TemplateSyntaxError('The %r option was specified more ' 'than once.' % option)
        if option == 'with':
            value = token_kwargs(remaining_bits, parser, support_legacy=False)
            if not value:
                raise TemplateSyntaxError(
                    '"with" in %r tag needs at least ' 'one keyword argument.' % bits[0]
                )
        elif option == 'only':
            value = True
        else:
            raise TemplateSyntaxError('Unknown argument for %r tag: %r.' % (bits[0], option))
        options[option] = value
    isolated_context = options.get('only', False)
    namemap = options.get('with', {})

    return FragmentNode(bits[1], extra_context=namemap, isolated_context=isolated_context)
