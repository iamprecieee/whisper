from django.urls import path
from .consumers import ChamberConsumer


websocket_urlpatterns = [
    path("ws/chamber/<str:chamber_id>/", ChamberConsumer.as_asgi()),
]