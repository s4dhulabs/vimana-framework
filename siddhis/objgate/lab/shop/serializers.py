# -*- coding: utf-8 -*-
from rest_framework import serializers

from shop.models import Order


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'owner', 'amount', 'note', 'secret')
        read_only_fields = ('id', 'owner')
