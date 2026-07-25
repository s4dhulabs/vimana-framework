# -*- coding: utf-8 -*-
"""Bearer token auth for objgate lab (maps tokens → usernames)."""

from rest_framework import authentication, exceptions

# token -> username
TOKENS = {
    'user-a-token': 'user-a',
    'user-b-token': 'user-b',
    'guest-token': 'guest',
}


class LabUser:
    is_authenticated = True
    is_staff = False
    is_superuser = False

    def __init__(self, username: str):
        self.username = username
        self.pk = username

    def __str__(self):
        return self.username


class BearerTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        header = request.META.get('HTTP_AUTHORIZATION', '')
        if not header:
            return None
        parts = header.split(' ', 1)
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        token = parts[1].strip()
        username = TOKENS.get(token)
        if not username:
            raise exceptions.AuthenticationFailed('Invalid token')
        return (LabUser(username), token)
