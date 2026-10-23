# -*- coding: utf-8 -*-
from django.urls import path

from blog.views import HealthView, SafeArticleView, VulnerableArticleView

urlpatterns = [
    path('health', HealthView.as_view()),
    path('health/', HealthView.as_view()),
    path('api/articles/', VulnerableArticleView.as_view()),
    path('api/articles/safe/', SafeArticleView.as_view()),
]
