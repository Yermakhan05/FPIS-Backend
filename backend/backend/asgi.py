"""
ASGI entry-point для Daphne / Uvicorn.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from chat.middleware import CustomAuthMiddlewareStack
import chat.routing
from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": CustomAuthMiddlewareStack(
            URLRouter(chat.routing.websocket_urlpatterns)
        ),
    }
)
