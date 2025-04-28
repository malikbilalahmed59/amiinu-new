from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model

User = get_user_model()


@database_sync_to_async
def get_user(token_key):
    try:
        # Validate the token using SimpleJWT
        token = AccessToken(token_key)
        user_id = token.payload['user_id']
        return User.objects.get(id=user_id)
    except (TokenError, User.DoesNotExist):
        return AnonymousUser()


class TokenAuthMiddleware:
    """
    Custom middleware that validates JWT token from query string
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Extract token from query string
        query_string = scope.get('query_string', b'').decode()
        token = None

        if query_string:
            # Parse query parameters
            params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
            token = params.get('token')

        # Get user from token
        scope['user'] = await get_user(token) if token else AnonymousUser()

        return await self.inner(scope, receive, send)