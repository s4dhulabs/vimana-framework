# -*- coding: utf-8 -*-
from rest_framework import serializers

from blog.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    """Public shape. Relations and author.note stay off the wire."""

    class Meta:
        model = Article
        fields = ('title', 'body')
