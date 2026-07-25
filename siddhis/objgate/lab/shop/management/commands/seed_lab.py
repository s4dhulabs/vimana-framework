# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from shop.models import Order


class Command(BaseCommand):
    help = 'Seed vulnerable orders for objgate lab'

    def handle(self, *args, **options):
        Order.objects.all().delete()
        Order.objects.create(
            id=1,
            owner='user-a',
            amount='42.00',
            note='order for user-a',
            secret='tenant-a-secret',
        )
        Order.objects.create(
            id=2,
            owner='user-b',
            amount='99.50',
            note='order for user-b',
            secret='tenant-b-secret',
        )
        Order.objects.create(
            id=3,
            owner='ops',
            amount='1000.00',
            note='admin-owned order',
            secret='ops-secret',
        )
        self.stdout.write(self.style.SUCCESS(f'Seeded {Order.objects.count()} orders'))
