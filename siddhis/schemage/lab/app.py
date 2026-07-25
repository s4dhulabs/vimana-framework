# -*- coding: utf-8 -*-
"""
Strawberry GraphQL lab for schemage.

Intentionally weak:
- introspection enabled
- no query depth/complexity limits
- order(id) returns any order without ownership check
- updateOrderNote mutation same BOLA
- unauthenticated queries allowed for order secrets
"""

from __future__ import annotations

from typing import Dict, List, Optional

import strawberry
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from strawberry.asgi import GraphQL


TOKENS = {
    'user-a-token': 'user-a',
    'user-b-token': 'user-b',
}

ORDERS: Dict[str, dict] = {
    '1': {
        'id': '1',
        'owner': 'user-a',
        'amount': 42.0,
        'note': 'order for user-a',
        'secret': 'tenant-a-secret',
    },
    '2': {
        'id': '2',
        'owner': 'user-b',
        'amount': 99.5,
        'note': 'order for user-b',
        'secret': 'tenant-b-secret',
    },
}


def _user_from_request(info) -> Optional[str]:
    request: Request = info.context['request']
    auth = request.headers.get('authorization') or ''
    if auth.lower().startswith('bearer '):
        token = auth.split(' ', 1)[1].strip()
        return TOKENS.get(token)
    return None


@strawberry.type
class User:
    username: str

    @strawberry.field
    def orders(self) -> List['Order']:
        return [
            Order(**{k: v for k, v in o.items() if k != 'owner'}, owner_name=o['owner'])
            for o in ORDERS.values()
            if o['owner'] == self.username
        ]


@strawberry.type
class Order:
    id: strawberry.ID
    amount: float
    note: str
    secret: str
    owner_name: strawberry.Private[str]

    @strawberry.field
    def owner(self) -> User:
        return User(username=self.owner_name)


def _order_type(data: dict) -> Order:
    return Order(
        id=strawberry.ID(data['id']),
        amount=float(data['amount']),
        note=data['note'],
        secret=data['secret'],
        owner_name=data['owner'],
    )


@strawberry.type
class Query:
    @strawberry.field
    def order(self, info: strawberry.Info, id: strawberry.ID) -> Optional[Order]:
        # BUG: no authz — any caller (even anonymous) gets any order incl. secret
        data = ORDERS.get(str(id))
        if not data:
            return None
        return _order_type(data)

    @strawberry.field
    def me(self, info: strawberry.Info) -> Optional[User]:
        username = _user_from_request(info)
        if not username:
            return None
        return User(username=username)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_order_note(
        self,
        info: strawberry.Info,
        id: strawberry.ID,
        note: str,
    ) -> Optional[Order]:
        # BUG: authenticated or not — no ownership check
        data = ORDERS.get(str(id))
        if not data:
            return None
        data['note'] = note
        return _order_type(data)


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQL(schema)


async def health(request: Request):
    return JSONResponse({'status': 'ok', 'service': 'schemage-lab'})


async def catalog(request: Request):
    return JSONResponse({
        'orders': list(ORDERS.values()),
        'tokens': {
            'user-a': 'Bearer user-a-token',
            'user-b': 'Bearer user-b-token',
        },
    })


app = Starlette(
    routes=[
        Route('/health', health),
        Route('/orders/catalog', catalog),
        # Both paths — Starlette Mount alone 307-redirects /graphql → /graphql/
        Route('/graphql', graphql_app),
        Route('/graphql/', graphql_app),
    ],
)
