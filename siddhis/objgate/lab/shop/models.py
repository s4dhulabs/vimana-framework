# -*- coding: utf-8 -*-
"""
Objgate lab models.

Intentionally weak authz on OrderViewSet (no owner filter).
"""

from django.db import models


class Order(models.Model):
    owner = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True, default='')
    secret = models.CharField(max_length=255, default='')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'Order#{self.pk} owner={self.owner}'
