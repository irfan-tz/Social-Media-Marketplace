from django.urls import re_path
from . import consumers

# websocket_urlpatterns = [
#     # re_path(r"ws/messages/$", consumers.MessageConsumer.as_asgi()),
#     # Irfan changed it from above to below
#     re_path(r'^ws/messages/$', consumers.MessageConsumer.as_asgi()),
# ]

websocket_urlpatterns = [
    re_path(r'^ws/messages/$', consumers.MessageConsumer.as_asgi()),
]
