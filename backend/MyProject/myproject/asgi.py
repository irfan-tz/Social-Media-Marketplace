import os
from django.core.asgi import get_asgi_application

# Set Django settings module first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Initialize Django before importing channels
django_asgi_app = get_asgi_application()

# Now import channels stuff
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from channels.db import database_sync_to_async
from django.conf import settings
from channels.middleware import BaseMiddleware
from django.db import close_old_connections
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

# Import routing after Django is initialized
from myapp import routing

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Close old database connections to prevent usage of timed out connections
        close_old_connections()

        # Get the token from cookies
        headers = dict(scope['headers'])
        cookies_header = next((h[1].decode() for h in scope['headers'] if h[0] == b'cookie'), '')
        cookies = {k: v for k, v in [cookie.split('=', 1) for cookie in cookies_header.split('; ') if '=' in cookie]}

        # Try to find the JWT token - check both access_token and token
        token = cookies.get('access_token', cookies.get('token', ''))

        # Set the user to anonymous by default
        scope['user'] = AnonymousUser()

        # Try to authenticate using the token
        if token:
            try:
                # Get the user ID from the token
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=['HS256']
                )
                user_id = payload.get('user_id')

                # Get the user
                if user_id:
                    User = get_user_model()
                    user = await self.get_user(user_id)
                    if user:
                        scope['user'] = user
            except Exception as e:
                # Invalid token, keep anonymous user
                pass
        else:
            pass

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

# Define the ASGI application with modified middleware stack
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter(
                routing.websocket_urlpatterns
            )
        )
    ),
})
