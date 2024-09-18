from django.urls import path
from .views import (
    ChamberListView,
    ChamberHTMLView,
)


app_name = "chat"
urlpatterns = [
    path("chamber-list/", ChamberListView.as_view(), name="chamber-list"),
    path("home/<str:chamber_id>/", ChamberHTMLView.as_view(), name="chamber-home"),
]
