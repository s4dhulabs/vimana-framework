# -*- coding: utf-8 -*-
from django.urls import include, path

urlpatterns = [
    path('', include('blog.urls')),
]
