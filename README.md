# Django View Fragments

This django app allows you to identify django template fragments that can be rendered independently by passing a query string to the view. This allows you to do fetch a fragment of a page, instead of the whole page, which means that you can do efficient AJAX updates to your page (triggered by e.g. a websocket event) really easily.

A simple example:

`yourapp/views.py`:

```py
from django.views.generic.base import TemplateView

from dvfragments.views import FragmentableTemplateViewMixin

class MyView(FragmentableTemplateViewMixin, TemplateView):
    template_name = 'yourapp/myview.html'

    # probably some methods like get_context_data() etc.
```

`yourapp/templates/yourapp/myview.html`:

```html
{% load static %}
{% load dvfragments %}
<!doctype html>
<html>
    <head>
        <script src="{% static 'dvfragments/reloadDVFragment.js' %}"></script>
    </head>
    <body>
        {% fragment if-frag %}
        {% if condition %}
        <p>Condition is true</p>
        {% else %}
        <p>Condition is false</p>
        {% endif %}
        {% endfragment %}
    </body>
</html>
```

Now say the view is mounted at `/myview`, If you do `GET /myview`, you will get the whole rendered template, but if you do: `GET /myview?fragment=if-frag` you get just the contents of the fragment, something like:

```html
<p>Condition is false</p>
```

Furthermore as a convenience, if you load the `dvfragments/reloadDVFragment.js` file (as above), then the function `window.reloadDVFragment(<fragment name>)` is added which will asynchronously fetch the specified fragment and replace the DOM node of that fragment with the updated version. This allows you to e.g. poll for updates, or use websockets to be notified when backend data has changed, such that you should reload a given fragment.
