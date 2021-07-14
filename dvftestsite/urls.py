from django.urls import path

from dvftestapp.views import View1

urlpatterns = [
    path('', View1.as_view(), name='view1'),
]
