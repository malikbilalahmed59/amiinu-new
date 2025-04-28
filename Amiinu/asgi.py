# Amiinu/asgi.py
"""
ASGI config for Amiinu project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

# Set environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Amiinu.settings')

# Initialize Django first
django.setup()

# Now import channels and your custom modules
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from notification.routing import websocket_urlpatterns
from notification.middleware import TokenAuthMiddleware

# Define the application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})