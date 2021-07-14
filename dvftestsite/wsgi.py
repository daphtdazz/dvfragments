"""
WSGI config for pardcards project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pardcards.settings')


def application(environ, start_response):
    os.environ.update({
        key: val for key, val in environ.items() if isinstance(val, str)
    })
    return get_wsgi_application()(environ, start_response)
