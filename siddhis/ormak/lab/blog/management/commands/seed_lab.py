# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from blog.models import Article, Author, Department

# Lowercase on purpose: SQLite LIKE folds case, so the lab canary
# is recoverable as this exact string even when the oracle is not byte-exact.
CANARY = 'ormnote'


class Command(BaseCommand):
    help = 'Seed the ormak ORM-leak lab'

    def handle(self, *args, **options):
        Article.objects.all().delete()
        Author.objects.all().delete()
        Department.objects.all().delete()
        User.objects.filter(username__in=('karen', 'jeff')).delete()

        news = Department.objects.create(name='news')
        desk = Department.objects.create(name='desk')

        karen_user = User.objects.create_user('karen', password='karen-lab')
        jeff_user = User.objects.create_user('jeff', password='jeff-lab')

        karen = Author.objects.create(user=karen_user, note=CANARY)
        jeff = Author.objects.create(user=jeff_user, note='othernote')
        karen.departments.add(news)
        jeff.departments.add(news, desk)

        Article.objects.create(
            title='Public Article',
            body='This is public',
            created_by=karen,
            is_secret=False,
        )
        Article.objects.create(
            title='Secret Article',
            body='This is secret',
            created_by=jeff,
            is_secret=True,
        )
        self.stdout.write(self.style.SUCCESS(
            f'Seeded {Article.objects.count()} articles, canary={CANARY}'
        ))
