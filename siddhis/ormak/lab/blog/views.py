# -*- coding: utf-8 -*-
"""
Two filters over the same Article queryset.

VulnerableArticleView unpacks the JSON body into QuerySet.filter.
SafeArticleView keeps an allowlist and never follows a relation.
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from blog.models import Article
from blog.serializers import ArticleSerializer

_ALLOWED = {'title', 'title__contains'}


def _articles(payload):
    try:
        rows = Article.objects.filter(**payload)
        return Response(ArticleSerializer(rows, many=True).data)
    except Exception:
        return Response([])


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({'status': 'ok'})


class VulnerableArticleView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        return _articles(payload)


class SafeArticleView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        if any(key not in _ALLOWED for key in payload):
            return Response([])
        return _articles(payload)
