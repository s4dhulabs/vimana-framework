# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    note = models.CharField(max_length=64, blank=True, default='')
    departments = models.ManyToManyField(Department, blank=True, related_name='authors')

    def __str__(self):
        return self.user.username


class Article(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    created_by = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='articles')
    is_secret = models.BooleanField(default=False)

    def __str__(self):
        return self.title
